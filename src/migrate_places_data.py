import csv
import uuid
from datetime import datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Optional

from loguru import logger
from sqlalchemy import text

from db.posgresql.connection import get_db_context
from db.posgresql.models.public.places import Place
from db.posgresql.repository.places import PlaceRepository
from db.posgresql import Base, engine


def parse_time(time_str: str) -> Optional[time]:
    """Parse time string in HH:MM format to time object"""
    if not time_str or time_str.strip() == "":
        return None
    try:
        # Handle 24-hour format (e.g., "23:59")
        if time_str == "23:59":
            return time(23, 59)
        elif time_str == "00:00":
            return time(0, 0)
        
        hour, minute = map(int, time_str.split(':'))
        return time(hour, minute)
    except (ValueError, AttributeError) as e:
        logger.warning(f"Could not parse time '{time_str}': {e}")
        return None


def parse_decimal(value_str: str) -> Optional[Decimal]:
    """Parse decimal string to Decimal object"""
    if not value_str or value_str.strip() == "" or value_str == "0":
        return None if value_str == "" else Decimal(value_str)
    try:
        return Decimal(value_str)
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse decimal '{value_str}': {e}")
        return None


def clean_description(description: str) -> str:
    """Clean description text"""
    if not description:
        return ""
    # Remove quotes if they wrap the entire string
    if description.startswith('"') and description.endswith('"'):
        description = description[1:-1]
    return description.strip()


def create_tables():
    """Create database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tables created successfully")
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        raise


def migrate_csv_to_db(csv_file_path: str) -> None:
    """Migrate data from CSV file to PostgreSQL database"""
    
    # Create tables first
    create_tables()
    
    csv_path = Path(csv_file_path)
    if not csv_path.exists():
        logger.error(f"❌ CSV file not found: {csv_file_path}")
        return

    with get_db_context() as session:
        repository = PlaceRepository(session)
        
        # Clear existing data (optional)
        logger.info("🧹 Clearing existing places data...")
        session.execute(text("DELETE FROM public.places"))
        session.commit()
        
        added_count = 0
        error_count = 0
        
        logger.info(f"📖 Reading CSV file: {csv_file_path}")
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 because row 1 is headers
                try:
                    # Skip empty rows or rows with missing required fields
                    if not row.get('name') or not row.get('latitude') or not row.get('longitude'):
                        logger.warning(f"⚠️ Skipping row {row_num}: missing required fields")
                        continue
                    
                    # Create Place object
                    place = Place(
                        id=uuid.uuid4(),  # Generate new UUID
                        name=row['name'].strip(),
                        description=clean_description(row.get('description', '')),
                        latitude=Decimal(row['latitude']),
                        longitude=Decimal(row['longitude']),
                        open_time=parse_time(row.get('open_time')),
                        close_time=parse_time(row.get('close_time')),
                        category=row.get('category', '').strip(),
                        rating=parse_decimal(row.get('rating', '')),
                        price_level=row.get('price_level', '').strip() if row.get('price_level', '').strip() else None,
                        price_average=parse_decimal(row.get('price_average', '')),
                        price_currency=row.get('price_currency', 'MXN').strip(),
                        address=clean_description(row.get('address', ''))
                    )
                    
                    # Add to database
                    repository.add(place)
                    added_count += 1
                    
                    if added_count % 50 == 0:
                        logger.info(f"📊 Added {added_count} places so far...")
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ Error processing row {row_num}: {e}")
                    logger.debug(f"Row data: {row}")
                    continue
    
    logger.info(f"""
🎉 Migration completed!
✅ Successfully added: {added_count} places
❌ Errors encountered: {error_count} rows
📍 Total places in database: {added_count}
    """)


def verify_migration():
    """Verify the migration by checking some statistics"""
    try:
        with get_db_context() as session:
            repository = PlaceRepository(session)
            
            total_count = repository.count()
            logger.info(f"📊 Total places in database: {total_count}")
            
            # Count by category
            categories = session.execute(
                text("SELECT category, COUNT(*) as count FROM public.places WHERE deleted_at IS NULL GROUP BY category ORDER BY count DESC")
            ).fetchall()
            
            logger.info("📈 Places by category:")
            for category, count in categories:
                logger.info(f"  - {category}: {count}")
                
            # Sample some places
            sample_places = repository.get_all(limit=5)
            logger.info("📋 Sample places:")
            for place in sample_places:
                logger.info(f"  - {place.name} ({place.category}) - Rating: {place.rating}")
                
    except Exception as e:
        logger.error(f"❌ Error verifying migration: {e}")


if __name__ == "__main__":
    logger.info("🚀 Starting places data migration...")
    
    # Path to CSV file (relative to project root)
    csv_file_path = "data_source.csv"
    
    try:
        migrate_csv_to_db(csv_file_path)
        verify_migration()
        logger.info("✅ Migration process completed successfully!")
        
    except Exception as e:
        logger.error(f"💥 Migration failed: {e}")
        raise 
import logging
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.contacts import  ContactCreate, ContactInDB, ContactUpdate, ContactBase
from src.database.models import Contact, User
from sqlalchemy import select, extract
from datetime import date, timedelta

# Создание логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Создание обработчика для вывода логов в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Создание форматировщика для логов
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Добавление обработчика к логгеру
logger.addHandler(console_handler)

async def create(body: ContactCreate, db: AsyncSession, user:User):
    """
    The create function creates a new contact in the database.
        Args:
            body (ContactCreate): The request body containing the information for creating a new contact.
            db (AsyncSession): The database session to use for querying and committing changes.
            user (User): The current user, used to determine which contacts belong to them.
    
    :param body: ContactCreate: Validate the body of the request
    :param db: AsyncSession: Create a database session
    :param user:User: Get the user id from the logged in user
    :return: A contact object
    :doc-author: Trelent
    """
    try:
        contact = Contact(**body.model_dump(), user_id=user.id)
        db.add(contact)
        await db.commit()
        await db.refresh(contact)
        return contact
    except Exception as e:
        logger.error(f"Error while creating contact: {e}")
        if "ValidationError" in str(e):
            logger.error("Validation error occurred.")
        raise HTTPException(status_code=500, detail="Internal Server Error")



async def get_contacts(limit: int, offset: int, db: AsyncSession, user:User):
    """
    The get_contacts function returns a list of contacts for the user.
    
    :param limit: int: Limit the number of contacts returned
    :param offset: int: Specify the number of records to skip before returning
    :param db: AsyncSession: Pass the database session to the function
    :param user:User: Filter the contacts by user_id
    :return: A list of contact objects
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(user_id=user.id).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_contact(contact_id: int, db: AsyncSession, user:User):
    """
    The get_contact function returns a contact object from the database.
        Args:
            contact_id (int): The id of the contact to be retrieved.
            db (AsyncSession): An async session for querying the database.
            user (User): The user who owns this contact.
    
    :param contact_id: int: Filter the query by id
    :param db: AsyncSession: Pass the database session to the function
    :param user:User: Check if the contact belongs to the user
    :return: A contact object
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(id=contact_id, user_id=user.id)
    contact = await db.execute(stmt)
    return contact.scalar_one_or_none()


async def update_contact(contact_id: int, body: ContactUpdate, db: AsyncSession, user:User):
    """
    The update_contact function updates a contact in the database.
        Args:
            contact_id (int): The id of the contact to update.
            body (ContactUpdate): The updated information for the Contact object.
            db (AsyncSession): An async session with an open transaction to use for querying and updating data in the database.
        Returns:
            Contact: A new instance of a Contact object with all fields populated from what was stored in the database.
    
    :param contact_id: int: Specify the contact that we want to update
    :param body: ContactUpdate: Pass in the information that is being updated
    :param db: AsyncSession: Pass the database session into the function
    :param user:User: Get the user_id from the database
    :return: A contact object
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(id=contact_id, user_id=user.id)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact:
        contact.first_name = body.first_name
        contact.last_name = body.last_name
        contact.email = body.email
        contact.phone_number = body.phone_number
        contact.birthday = body.birthday
        await db.commit()
        await db.refresh(contact)
    return contact


async def delete_contact(contact_id: int, db: AsyncSession, user:User):
    """
    The delete_contact function deletes a contact from the database.
        Args:
            contact_id (int): The id of the contact to delete.
            db (AsyncSession): An async session object for interacting with the database.
            user (User): The user who is deleting this contact, used to ensure that only contacts belonging to this user are deleted.
    
    :param contact_id: int: Identify the contact to be deleted
    :param db: AsyncSession: Pass in the database connection
    :param user:User: Get the user_id of the contact to be deleted
    :return: The contact object that was deleted
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(id=contact_id, user_id=user.id)
    contact = await db.execute(stmt)
    contact = contact.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact



async def get_birthdays(days, db: AsyncSession, user:User):
    """
    The get_birthdays function returns a list of contacts that have birthdays within the next `days` days.
    
    :param days: Determine how many days in the future to look for birthdays
    :param db: AsyncSession: Pass the database session to the function
    :param user:User: Filter the contacts by user
    :return: A list of contacts
    :doc-author: Trelent
    """
    days:int = days + 1
    filter_month = date.today().month
    filter_day = date.today().day
    
    stmt = select(Contact).filter(
        Contact.user_id == user.id,
        extract('month', Contact.birthday) == filter_month,
        extract('day', Contact.birthday) <= filter_day + days
    )
    
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def search(first_name, last_name, email, skip, limit, db, user:User):
    """
    The search function searches for contacts in the database.
    
    :param first_name: Filter contacts by first name
    :param last_name: Filter the result by last name
    :param email: Filter the contacts by email
    :param skip: Skip the first n records in a query result
    :param limit: Limit the number of records returned by the query
    :param db: Pass the database connection to the function
    :param user:User: Pass the user object to the function
    :return: A list of objects
    :doc-author: Trelent
    """
    query = select(Contact).filter_by(user_id=user.id)
    if first_name:
        query = query.filter(Contact.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.filter(Contact.last_name.ilike(f"%{last_name}%"))   
    if email:
        query = query.filter(Contact.email.ilike(f"%{email}%"))   
    
    result_query = query.offset(skip).limit(limit)
    
    try:
        contacts = await db.execute(result_query)
        return contacts.scalars().all()
    except Exception as e:
        # Обработка исключения, запись ошибки в журнал и возврат соответствующего ответа
        print(f"Ошибка при выполнении запроса к базе данных: {e}")
        return []



    
  
    

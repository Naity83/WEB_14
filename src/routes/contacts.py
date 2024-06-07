import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.schemas.contacts import ContactBase, ContactCreate, ContactInDB, ContactUpdate
from src.repository import contacts as repository_contacts
from sqlalchemy import or_, select
from src.database.models import Contact, User
from datetime import date, timedelta
from src.services.auth import auth_service


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

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=list[ContactInDB])
async def get_contacts(limit: int = Query(10, ge=10, le=500),
                        offset: int = Query(0, ge=0),
                    db: AsyncSession = Depends(get_db),
                    user: User = Depends(auth_service.get_current_user)):
    """
    The get_contacts function returns a list of contacts for the current user.
        The limit and offset parameters are used to paginate the results.
    
    
    :param limit: int: Limit the number of contacts returned
    :param ge: Specify a minimum value for the limit parameter
    :param le: Limit the number of contacts returned to 500
    :param offset: int: Skip the first n contacts, where n is the offset
    :param ge: Check if the limit is greater than or equal to 10
    :param db: AsyncSession: Pass the database session to the repository layer
    :param user: User: Get the user id from the token
    :return: A list of contact objects
    :doc-author: Trelent
    """
    contacts = await repository_contacts.get_contacts(limit, offset, db, user)
    return contacts


@router.post("/", response_model=ContactInDB, status_code=status.HTTP_201_CREATED)
async def create_contact(contact_data: ContactCreate, 
                         db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):
    """
    The create_contact function creates a new contact.
    
    :param contact_data: ContactCreate: Pass the contact data to be created
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the current user from the auth_service
    :return: A contact object, but the schema is not defined
    :doc-author: Trelent
    """
    try:
        contact = await repository_contacts.create(contact_data, db, user)
        return contact
    except Exception as e:
        logger.error(f"Error while creating contact: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")


@router.get("/birthday", response_model=list[ContactInDB])
async def get_birthdays(days: int = Query(7, ge=7),
                         db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):
    """
    The get_birthdays function returns a list of contacts with birthdays in the next 7 days.
    
    :param days: int: Specify the number of days to look ahead for birthdays
    :param ge: Specify that the days parameter must be greater than or equal to 7
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the current user
    :return: A list of contacts
    :doc-author: Trelent
    """
    contacts = await repository_contacts.get_birthdays(days, db, user)
    return contacts


@router.get("/search", response_model=list[ContactInDB])
async def serch(
    first_name: str = None,
    last_name: str = None,
    email: str = None,
    skip: int = 0,
    limit: int = Query(default=10, le=100, ge=10),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
):
    """
    The serch function searches for contacts in the database.
        Args:
            first_name (str): The first name of the contact to search for.
            last_name (str): The last name of the contact to search for.
            email (str): The email address of the contact to search for.
            skip (int, optional): Number of records to skip before returning results, defaults to 0 if not provided or None is provided as a value.. Defaults to 0.
            limit ([type], optional): Maximum number of records returned by this function, defaults 10 if not provided or
    
    :param first_name: str: Search for a contact by first name
    :param last_name: str: Filter the contacts by last name
    :param email: str: Search for a contact by email
    :param skip: int: Skip the first x number of records
    :param limit: int: Limit the number of results returned
    :param le: Limit the number of results returned
    :param ge: Set a minimum value for the limit parameter
    :param db: AsyncSession: Get the database connection
    :param user: User: Get the user from the database
    :return: A list of contacts, but the schema is expecting a single contact
    :doc-author: Trelent
    """
    contacts = await repository_contacts.search(first_name, last_name, email, skip, limit, db, user)
    return contacts
    
@router.get("/{contact_id}", response_model=ContactInDB)
async def get_contact(contact_id: int = Path(ge=1), 
                      db: AsyncSession = Depends(get_db),
                      user: User = Depends(auth_service.get_current_user)):
    """
    The get_contact function returns a contact by id.
        Args:
            contact_id (int): The id of the contact to return.
            db (AsyncSession): An async database session object.
            user (User): A User object containing information about the current user, including their role and permissions.
        Returns: 
            Contact: A Contact object containing information about a single contact.
    
    :param contact_id: int: Get the contact id from the path
    :param db: AsyncSession: Pass the database connection to the function
    :param user: User: Get the current user
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repository_contacts.get_contact(contact_id, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contact


@router.put("/{contact_id}")
async def update_contact(body: ContactUpdate, 
                         contact_id: int = Path(ge=1), 
                         db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):
    """
    The update_contact function updates a contact in the database.
        The function takes an id, body and db as parameters.
        It returns the updated contact.
    
    :param body: ContactUpdate: Get the data from the body of the request
    :param contact_id: int: Get the contact id from the url
    :param db: AsyncSession: Pass the database session to the repository layer
    :param user: User: Get the current user from the auth_service
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repository_contacts.update_contact(contact_id, body, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: int = Path(ge=1), 
                         db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):
    contact = await repository_contacts.delete_contact(contact_id, db, user)
    return contact









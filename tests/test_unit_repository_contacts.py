import unittest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from src.database.models import User, Contact
from src.schemas.contacts import ContactCreate, ContactUpdate
from src.repository.contacts import (
    create,
    get_contacts,
    get_contact,
    update_contact,
    delete_contact,
    get_birthdays,
    search
)

class TestContactRepository(unittest.IsolatedAsyncioTestCase):

    
    async def test_create_contact(self):
        # Mocking the database session
        session = MagicMock(spec=AsyncSession)
        # Mocking the user object
        user = MagicMock(spec=User)
        user.id = 1  # Установка атрибута id для пользователя

        # Test parameters
        body = ContactCreate(first_name="John", last_name="Doe", email="john@example.com", phone_number="1234567890", birthday="1990-01-01")

        # Calling the function under test
        result = await create(body, session, user)

        # Verifying that the contact is created
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)

    async def test_get_contacts(self):
        session = AsyncMock(spec=AsyncSession)
        limit = 10
        offset = 0
        user = User(id=1)
        contact = Contact(id=1, user_id=user.id, first_name="Test", last_name="Contact", email="test@example.com")
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[contact])))
        session.execute = AsyncMock(return_value=mock_result)
        result = await get_contacts(limit, offset, session, user)
        self.assertEqual(result, [contact])

    async def test_get_contact(self):
        session = AsyncMock(spec=AsyncSession)
        contact_id = 1
        user = User(id=1)
        contact = Contact(id=contact_id, user_id=user.id, first_name="Test", last_name="Contact", email="test@example.com")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = contact
        session.execute = AsyncMock(return_value=mock_result)
        result = await get_contact(contact_id, session, user)
        self.assertEqual(result, contact)

    async def test_update_contact(self):
        session = AsyncMock(spec=AsyncSession)
        contact_id = 1
        user = User(id=1)
        body = ContactUpdate(
            first_name="Jane", 
            last_name="Doe", 
            email="jane@example.com", 
            phone_number="1234567890", 
            birthday="1990-02-02"
        )
        contact = Contact(
            id=contact_id, 
            first_name="John", 
            last_name="Doe", 
            email="john@example.com", 
            phone_number="1234567890", 
            birthday="1990-01-01", 
            user_id=user.id
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = contact
        session.execute = AsyncMock(return_value=mock_result)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        result = await update_contact(contact_id, body, session, user)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone_number, body.phone_number)
        self.assertEqual(result.birthday, body.birthday)

    async def test_delete_contact(self):
        session = AsyncMock(spec=AsyncSession)
        contact_id = 1
        user = User(id=1)
        contact = Contact(id=contact_id, user_id=user.id)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = contact
        session.execute = AsyncMock(return_value=mock_result)
        session.delete = AsyncMock()
        session.commit = AsyncMock()
        result = await delete_contact(contact_id, session, user)
        self.assertEqual(result, contact)

    async def test_get_birthdays(self):
        session = AsyncMock(spec=AsyncSession)
        days = 7
        user = User(id=1)
        today = date.today()
        contacts = [
            Contact(birthday=today + timedelta(days=i), user_id=user.id) for i in range(5)
        ]
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=contacts)))
        session.execute = AsyncMock(return_value=mock_result)
        result = await get_birthdays(days, session, user)
        expected_contacts = contacts[:days+1]
        self.assertEqual(result, expected_contacts)

    async def test_search(self):
        session = AsyncMock(spec=AsyncSession)
        user = User(id=1)
        first_name = "John"
        last_name = "Doe"
        email = "john@example.com"
        skip = 0
        limit = 10
        contact = Contact(id=1, first_name=first_name, last_name=last_name, email=email, user_id=user.id)
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[contact])))
        session.execute = AsyncMock(return_value=mock_result)
        result = await search(first_name, last_name, email, skip, limit, session, user)
        self.assertEqual(result, [contact])

if __name__ == '__main__':
    unittest.main()




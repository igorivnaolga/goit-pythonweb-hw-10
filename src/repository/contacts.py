from typing import List, Self, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, delete, extract, or_, and_
from sqlalchemy.sql import extract
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas.contacts import ContactBase, ContactUpdate


class ContactRepository:
    def __init__(self: Self, session: AsyncSession):
        self.db = session

    async def get_contacts(
        self: Self,
        skip: int,
        limit: int,
        name: str | None,
        surname: str | None,
        email: str | None,
        user: User,
    ) -> List[Contact]:
        stmt = select(Contact)
        if name:
            stmt = stmt.filter_by(first_name=name, user=user)
        if surname:
            stmt = stmt.filter_by(last_name=surname, user=user)
        if email:
            stmt = stmt.filter_by(email=email, user=user)
        stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_contact(self: Self, contact_id: int, user=User) -> Contact | None:
        stmt = select(Contact).filter_by(id=contact_id, user=user)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_contact(
        self: Self, body: ContactBase, user=User
    ) -> Contact | None:
        contact = Contact(**body.model_dump(exclude_unset=True), user=User)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def delete_contact(self: Self, contact_id: int, user: User) -> None:
        contact = await self.get_contact(contact_id, user)
        if contact is None:
            return None
        stmt = delete(Contact).where(Contact.id == contact_id)
        await self.db.execute(stmt)
        await self.db.commit()
        return True

    # async def update_contact(
    #     self: Self, contact_id: int, body: ContactBase
    # ) -> Contact | None:
    #     contact = await self.get_contact(contact_id)
    #     if contact:
    #         for key, value in body.model_dump().items():
    #             setattr(contact, key, value)
    #         await self.db.commit()
    #         await self.db.refresh(contact)
    #     return contact

    async def update_contact(
        self, contact_id: int, user: User, body: ContactUpdate
    ) -> Contact | None:
        contact = await self.get_contact(contact_id, user)
        if contact:
            for key, value in body.model_dump(exclude_unset=True).items():
                setattr(contact, key, value)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def get_birthdays(self: Self, skip: int, limit: int) -> List[Contact]:
        today = datetime.now().date()
        today_month = today.month
        today_day = today.day

        end_date = today + timedelta(days=7)
        end_month = end_date.month
        end_day = end_date.day

        stmt = (
            select(Contact)
            .filter(
                or_(
                    and_(
                        extract("month", Contact.birthday) == today_month,
                        extract("day", Contact.birthday) >= today_day,
                    ),
                    and_(
                        extract("month", Contact.birthday) == end_month,
                        extract("day", Contact.birthday) <= end_day,
                    ),
                    # якщо перехід через грудень → січень
                    and_(
                        extract("month", Contact.birthday) == 1,
                        today_month == 12,
                        extract("day", Contact.birthday) <= end_day,
                    ),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

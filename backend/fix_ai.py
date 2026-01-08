import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from server import analyze_document_with_ai

async def main():
    db = AsyncIOMotorClient(os.getenv("MONGO_URL"))[os.getenv("DB_NAME")]
    templates = await db.templates.find({}).to_list(1000)

    for t in templates:
        ai = await analyze_document_with_ai(
            t["content"],
            t["structure_data"],
            t["file_type"]
        )

        await db.templates.update_one(
            {"id": t["id"]},
            {"$set": {"structure_data.ai_analysis": ai}}
        )
        print(f"✅ Updated AI for: {t['name']}")

asyncio.run(main())

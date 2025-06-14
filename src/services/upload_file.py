import cloudinary
import cloudinary.uploader
import asyncio


class UploadFileService:
    def __init__(self, cloud_name, api_key, api_secret):
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )

    async def upload_file(self, file, username: str) -> str:
        public_id = f"ContactsApp/{username}"
        content = await file.read()

        # Завантаження в окремому потоці, щоб не блокувати event loop
        r = await asyncio.to_thread(
            cloudinary.uploader.upload,
            content,
            public_id=public_id,
            overwrite=True,
        )

        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url

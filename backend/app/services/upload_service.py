import logging
import os
import uuid
import hashlib
import filetype
from fastapi import UploadFile, HTTPException, status
import cloudinary
import cloudinary.uploader
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure Cloudinary if credentials are present
CLOUDINARY_CONFIGURED = False
if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
    try:
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )
        CLOUDINARY_CONFIGURED = True
        logger.info("Cloudinary configured successfully.")
    except Exception as e:
        logger.error(f"Failed to configure Cloudinary: {e}")


async def validate_and_hash_file(file: UploadFile, is_video: bool = False) -> tuple[bytes, str, str]:
    """Read file content, validate size & MIME type from bytes, and generate SHA-256 hash."""
    contents = await file.read()
    # Reset file pointer so other libraries/methods can read from it if needed
    file.file.seek(0)
    
    size = len(contents)
    max_size = 50 * 1024 * 1024 if is_video else 10 * 1024 * 1024
    if size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds limit of {max_size // (1024 * 1024)}MB."
        )

    # Detect file type from magic bytes
    kind = filetype.guess(contents)
    if not kind:
        # Fallback to checking file extension if byte guess fails for small/plain headers
        filename = file.filename or ""
        ext = os.path.splitext(filename)[1].lower()
        if is_video and ext in [".mp4", ".webm"]:
            mime = f"video/{ext[1:]}"
        elif not is_video and ext in [".jpg", ".jpeg", ".png", ".webp"]:
            mime = f"image/{ext[1:]}"
            if ext == ".jpg":
                mime = "image/jpeg"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not determine file type from byte signature."
            )
    else:
        mime = kind.mime

    allowed_images = ["image/jpeg", "image/png", "image/webp"]
    allowed_videos = ["video/mp4", "video/webm"]

    if is_video:
        if mime not in allowed_videos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported video format: {mime}. Allowed: MP4, WEBM."
            )
    else:
        if mime not in allowed_images:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported image format: {mime}. Allowed: JPG, JPEG, PNG, WEBP."
            )

    # Compute SHA-256 hash
    sha256 = hashlib.sha256(contents).hexdigest()
    return contents, mime, sha256


async def upload_image(file: UploadFile) -> tuple[str, str]:
    """Validate, hash and upload an image file. Returns (public_url, sha256_hash)."""
    contents, mime, sha256_hash = await validate_and_hash_file(file, is_video=False)

    if CLOUDINARY_CONFIGURED:
        try:
            upload_result = cloudinary.uploader.upload(
                contents,
                folder="nagarik/images",
                resource_type="image"
            )
            url = upload_result.get("secure_url")
            return url, sha256_hash
        except Exception as e:
            logger.error(f"Cloudinary image upload failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Cloudinary upload failed: {str(e)}"
            )
    else:
        logger.warning("Cloudinary not configured! Using mock image upload.")
        # Return a deterministic placeholder URL based on file hash
        return f"https://picsum.photos/seed/{sha256_hash[:8]}/800/600", sha256_hash


async def upload_video(file: UploadFile) -> tuple[str, str]:
    """Validate, hash and upload a video file. Returns (public_url, sha256_hash)."""
    contents, mime, sha256_hash = await validate_and_hash_file(file, is_video=True)

    if CLOUDINARY_CONFIGURED:
        try:
            upload_result = cloudinary.uploader.upload(
                contents,
                folder="nagarik/videos",
                resource_type="video"
            )
            url = upload_result.get("secure_url")
            return url, sha256_hash
        except Exception as e:
            logger.error(f"Cloudinary video upload failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Cloudinary video upload failed: {str(e)}"
            )
    else:
        logger.warning("Cloudinary not configured! Using mock video upload.")
        return "https://www.w3schools.com/html/mov_bbb.mp4", sha256_hash

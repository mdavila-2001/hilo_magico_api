import os
import uuid
from fastapi import UploadFile, HTTPException
import shutil
from typing import Optional, Set
import logging

from app.core.config import settings


logger = logging.getLogger(__name__)

class FileService:
    """Servicio para manejar la subida y gestión de archivos"""
    
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.allowed_extensions = set(settings.ALLOWED_EXTENSIONS.split(','))
        self.max_size_mb = settings.MAX_FILE_SIZE  # Tamaño máximo de archivo en MB
        
    def _ensure_upload_dir_exists(self, subfolder: str = "") -> str:
        """Asegura que el directorio de subida exista"""
        upload_path = os.path.join(self.upload_dir, subfolder)
        os.makedirs(upload_path, exist_ok=True)
        return upload_path
    
    def _get_file_extension(self, filename: str) -> str:
        """Obtiene la extensión de un archivo en minúsculas"""
        return os.path.splitext(filename)[1][1:].lower()
    
    def is_valid_extension(self, filename: str) -> bool:
        """Verifica si la extensión del archivo está permitida"""
        if not filename:
            return False
        ext = self._get_file_extension(filename)
        return ext in self.allowed_extensions
    
    def is_valid_size(self, file: UploadFile) -> bool:
        """Verifica si el tamaño del archivo es válido"""
        # Mover el cursor al final del archivo para obtener su tamaño
        file.file.seek(0, 2)
        file_size = file.file.tell()
        # Volver al inicio del archivo
        file.file.seek(0)
        
        max_size_bytes = self.max_size_mb * 1024 * 1024  # Convertir MB a bytes
        return file_size <= max_size_bytes
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        """Genera un nombre de archivo único"""
        ext = self._get_file_extension(original_filename)
        unique_id = str(uuid.uuid4())
        return f"{unique_id}.{ext}"
    
    async def save_upload_file(self, file: UploadFile, subfolder: str = "") -> str:
        """
        Guarda un archivo subido en el sistema de archivos
        
        Args:
            file: Archivo a guardar (FastAPI UploadFile)
            subfolder: Subcarpeta dentro del directorio de subidas
            
        Returns:
            Ruta relativa al archivo guardado
            
        Raises:
            HTTPException: Si el archivo no es válido o hay un error al guardar
        """
        try:
            # Validar archivo
            if not file:
                raise HTTPException(status_code=400, detail="No se proporcionó ningún archivo")
                
            if not self.is_valid_extension(file.filename):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Extensión de archivo no permitida. Extensiones permitidas: {', '.join(self.allowed_extensions)}"
                )
                
            if not self.is_valid_size(file):
                raise HTTPException(
                    status_code=400,
                    detail=f"El archivo es demasiado grande. Tamaño máximo: {self.max_size_mb}MB"
                )
            
            # Crear directorio si no existe
            upload_path = self._ensure_upload_dir_exists(subfolder)
            
            # Generar nombre único para el archivo
            unique_filename = self._generate_unique_filename(file.filename)
            file_path = os.path.join(upload_path, unique_filename)
            
            # Guardar archivo
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Retornar ruta relativa
            return os.path.join("static", "uploads", subfolder, unique_filename).replace("\\", "/")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error al guardar archivo: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error al guardar el archivo: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        """
        Elimina un archivo del sistema de archivos
        
        Args:
            file_path: Ruta relativa o absoluta al archivo
            
        Returns:
            bool: True si se eliminó correctamente, False si no existía
        """
        try:
            # Convertir a ruta absoluta si es relativa
            if not os.path.isabs(file_path):
                file_path = os.path.join(os.getcwd(), file_path)
                
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Error al eliminar archivo {file_path}: {str(e)}")
            return False

# Instancia global del servicio
file_service = FileService()

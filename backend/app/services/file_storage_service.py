"""
File Storage Service for local filesystem operations.

This service replaces Firebase Storage with local filesystem storage,
providing secure file operations with path validation and unique filename generation.

Feature: firebase-to-sqlite-migration
Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
"""

import os
from pathlib import Path
from typing import Optional
import uuid


class FileStorageService:
    """Service for managing local file storage with security checks."""
    
    def __init__(self, storage_root: str):
        """
        Initialize the file storage service.
        
        Args:
            storage_root: Root directory for file storage
        """
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)
    
    def save_file(self, file_content: bytes, application_id: str, filename: str) -> str:
        """
        Save a file to local storage and return the file path.
        
        Args:
            file_content: Binary content of the file
            application_id: ID of the application (used for directory organization)
            filename: Original filename
            
        Returns:
            Relative path from storage root to the saved file
            
        Raises:
            ValueError: If filename is invalid
        """
        # Create application-specific directory
        app_dir = self.storage_root / application_id
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize and generate unique filename
        safe_filename = self._sanitize_filename(filename)
        file_path = app_dir / safe_filename
        
        # Generate unique filename if file already exists
        counter = 1
        name, ext = os.path.splitext(safe_filename)
        while file_path.exists():
            file_path = app_dir / f"{name}_{counter}{ext}"
            counter += 1
        
        # Write file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Return relative path from storage root
        return str(file_path.relative_to(self.storage_root))
    
    def read_file(self, file_path: str) -> bytes:
        """
        Read a file from local storage.
        
        Args:
            file_path: Relative path from storage root
            
        Returns:
            Binary content of the file
            
        Raises:
            ValueError: If file path is invalid or contains directory traversal
            FileNotFoundError: If file does not exist
        """
        full_path = self.storage_root / file_path
        
        # Validate path security
        if not self._is_safe_path(full_path):
            raise ValueError("Invalid file path: directory traversal detected")
        
        # Read and return file content
        with open(full_path, 'rb') as f:
            return f.read()
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from local storage.
        
        Args:
            file_path: Relative path from storage root
            
        Returns:
            True if file was deleted, False if file did not exist
            
        Raises:
            ValueError: If file path is invalid or contains directory traversal
        """
        full_path = self.storage_root / file_path
        
        # Validate path security
        if not self._is_safe_path(full_path):
            raise ValueError("Invalid file path: directory traversal detected")
        
        # Delete file if it exists
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal and invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename (basename only, no path components)
        """
        # Extract basename to remove any path components
        safe_name = os.path.basename(filename)
        
        # If filename is empty or only contains path separators, generate a unique name
        if not safe_name or safe_name in ('.', '..'):
            safe_name = f"file_{uuid.uuid4().hex[:8]}"
        
        return safe_name
    
    def _is_safe_path(self, path: Path) -> bool:
        """
        Check if path is within storage root to prevent directory traversal.
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is safe (within storage root), False otherwise
        """
        try:
            # Resolve both paths to absolute paths and check if file path is within storage root
            resolved_path = path.resolve()
            resolved_root = self.storage_root.resolve()
            resolved_path.relative_to(resolved_root)
            return True
        except (ValueError, RuntimeError):
            # ValueError: path is not relative to storage root
            # RuntimeError: infinite loop in path resolution (symlink cycles)
            return False

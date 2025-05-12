import hashlib
import secrets
from datetime import datetime
from app.utils.db import db

class UserORM(db.Model):
    """SQLAlchemy ORM model for users table"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    salt = db.Column(db.String(32), nullable=False)
    is_admin = db.Column(db.Integer, default=0)
    created_at = db.Column(db.String(32), default=lambda: datetime.now().isoformat())
    
    def __init__(self, username=None, password=None, salt=None, is_admin=0, created_at=None):
        """Initialize a new user"""
        self.username = username
        self.password = password
        self.salt = salt
        self.is_admin = is_admin
        self.created_at = created_at or datetime.now().isoformat()
        
        if password and not salt:
            self.set_password(password)
    
    @staticmethod
    def hash_password(password, salt=None):
        """Hash a password for storing"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use SHA-256 for password hashing
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash, salt
    
    @staticmethod
    def verify_password(stored_password, stored_salt, provided_password):
        """Verify a stored password against one provided by user"""
        return stored_password == hashlib.sha256((provided_password + stored_salt).encode()).hexdigest()
    
    def set_password(self, password):
        """Set the password for this user"""
        password_hash, salt = self.hash_password(password)
        self.password = password_hash
        self.salt = salt
    
    def check_password(self, password):
        """Check if the provided password is correct"""
        return self.verify_password(self.password, self.salt, password)
    
    def toggle_admin(self, is_admin):
        """Toggle admin status for this user"""
        self.is_admin = is_admin
        db.session.commit()
        return True
    
    @classmethod
    def get_by_id(cls, user_id):
        """Get a user by ID"""
        return db.session.get(cls, user_id)
    
    @classmethod
    def get_by_username(cls, username):
        """Get a user by username"""
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def get_all(cls):
        """Get all users"""
        users = cls.query.all()
        return [user.to_dict() for user in users]
    
    @classmethod
    def exists(cls, username):
        """Check if a user with the given username exists"""
        return cls.query.filter_by(username=username).first() is not None
    
    def save(self):
        """Save the user to the database"""
        # Set password hash and salt if not already set
        if self.password and not self.salt:
            self.set_password(self.password)
        
        db.session.add(self)
        db.session.commit()
        return self.id
    
    def delete(self):
        """Delete the user from the database"""
        if not self.id:
            return False
        
        db.session.delete(self)
        db.session.commit()
        return True
    
    def to_dict(self, include_sensitive=False):
        """Convert User object to dictionary"""
        result = {
            'id': self.id,
            'username': self.username,
            'is_admin': self.is_admin,
            'created_at': self.created_at
        }
        
        # Include sensitive information if requested
        if include_sensitive:
            result['password'] = self.password
            result['salt'] = self.salt
            
        return result
import os
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any


class Settings(BaseSettings):
    # データベース設定
    DB_USER: str = "fx_user"
    DB_PASSWORD: str = "fx_password"
    DB_HOST: str = "postgres"
    DB_PORT: str = "5432"
    DB_NAME: str = "fx_trader_db"
    
    @property
    def DATABASE_URL(self) -> str:
        """動的にデータベースURLを生成"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # テスト用データベースURL
    TEST_DATABASE_URL: Optional[str] = None
    
    # アプリケーション設定
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True
        extra = 'ignore'  # 未定義の環境変数を無視


# 設定のインスタンス化
settings = Settings()

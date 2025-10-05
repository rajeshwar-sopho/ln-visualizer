from typer.testing import CliRunner
from src.main import app, AppConfig

runner = CliRunner()


def test_hello_default():
    """Test hello command with default name"""
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Hello World!" in result.stdout
    assert "Setup verified!" in result.stdout


def test_hello_custom_name():
    """Test hello command with custom name"""
    result = runner.invoke(app, ["--name", "Alice"])
    assert result.exit_code == 0
    assert "Hello Alice!" in result.stdout


def test_app_config_model():
    """Test AppConfig Pydantic model"""
    config = AppConfig(api_key="test_key_123")
    assert config.api_key == "test_key_123"
    
    # Test with None
    config_empty = AppConfig()
    assert config_empty.api_key is None


def test_app_config_validation():
    """Test AppConfig model validation"""
    # Should accept None or string
    config1 = AppConfig(api_key=None)
    assert config1.api_key is None
    
    config2 = AppConfig(api_key="sk-123456")
    assert config2.api_key == "sk-123456"
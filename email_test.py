from src.core.config.config import settings
from src.core.services.email.email import EmailService

def test_delivery():
    test_cases = [
        ("your.personal@gmail.com", "Personal Gmail"),
        ("your.work@company.com", "Work Email"),
        ("free@yahoo.com", "Yahoo Mail"),
        ("proton@protonmail.com", "ProtonMail")
    ]
    
    for email, name in test_cases:
        success = EmailService.send_email(
            to_email=email,
            subject=f"Delivery Test to {name}",
            body=f"Testing delivery to {email}"
        )
        print(f"{name}: {'✅' if success else '❌'}")

test_delivery()
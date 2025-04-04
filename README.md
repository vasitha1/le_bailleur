# LeBailleur: WhatsApp-Integrated Property Management System

## Project Inspiration

LeBailleur was born from witnessing the daily struggles of my 79-year-old father managing his rental properties. His challenges included:

- **Tracking multiple payment streams** (rent, electricity, Wi-Fi)
- **Managing extensive receipt documentation** for 80+ tenants
- **Keeping track of complex rent cycles** with different due dates
- **Communicating promptly** with tenants about payments and issues

When creating it, I also made use of phone number based authentication,so as to resolve not only a personal problem but also  a tool that could help property owners of all sizes simplify their rental management process.

## Overview

LeBailleur is a Django-based property management system with WhatsApp integration, designed to streamline communication between landlords and tenants. The application allows landlords to manage properties, track rent payments, and automate notifications through a familiar messaging platform that both parties already use daily.

## Key Features

- **WhatsApp-First Interface**: Manage everything through conversational commands
- **Automated Rent Reminders**: Notify tenants and landlords when payments are due
- **Payment Tracking**: Monitor rent status across all properties and tenants
- **Digital Receipts**: Automatically generate receipts upon payment confirmation
- **Multi-Property Support**: Manage multiple properties from a single account
- **Payment Plan Management**: Allow tenants to request payment extensions
- **User-Friendly Navigation**: Simple numeric menu system for easy operation

## Tech Stack

- **Backend**: Django, Django REST Framework
- **Communication**: WhatsApp Business API
- **Deployment**: Render
- **Database**: SQLight(for a begining)

## System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────┐
│  WhatsApp User  │◄────┤  WhatsApp API    │◄────┤  RentTrack    │
│  (Landlord or   │     │                  │     │  Django App   │
│   Tenant)       │────►│                  │────►│               │
└─────────────────┘     └──────────────────┘     └───────┬───────┘
                                                         │
                                                         │
                                                         ▼
                                                  ┌───────────────┐
                                                    │
                                                  │  Database     │
                                                  └───────────────┘
```

## User Flow

### Landlord Registration
1. Send message to RentTrack's WhatsApp number (+1 555 631 1809)
2. Select landlord role (option 1)
3. Complete registration by providing name
4. Register properties, rent entities, and tenants

### Tenant Experience
1. Receive registration confirmation when added by landlord
2. Get automated rent reminders when payments are due
3. Respond with payment status or request extensions
4. Receive digital receipts upon payment confirmation

### Landlord Dashboard Options
1. Register/delete properties
2. Register/delete rent entities
3. Register/delete tenants
4. View rent status (all tenants, owing tenants, specific tenant)
5. Update payment status and generate receipts
6. Access customer support

## API Endpoints

The application exposes several RESTful API endpoints:

```
# Core endpoints
/d11c683a-1ec0-4a7d-b69f-d99cb67ceed0/     # Home view
/webhook/                                   # WhatsApp webhook verification
/api/webhook/                               # WhatsApp message processing

# Property management
/properties/                                # List & create properties
/properties/<id>/                           # Retrieve, update, delete properties
/properties/manage/                         # Property management options
/properties/delete/<id>/                    # Property deletion selection
/properties/delete/confirm/<id>/            # Property deletion confirmation

# Rent entity management
/rent-entities/                             # List & create rent entities
/rent-entities/<id>/                        # Retrieve, update, delete rent entities

# Tenant management
/tenants/                                   # List & create tenants
/tenants/<id>/                              # Retrieve, update, delete tenants

# Landlord management
/landlords/create/                          # Create landlord
/landlords/                                 # List landlords
/landlords/<id>/                            # Retrieve, update, delete landlords

# Payment processing
/payments/confirm/                          # Payment confirmation
/payments/modify/                           # Payment modification
```

## Installation and Setup

### Prerequisites
- Python 3.8+
- Django 4.0+
- WhatsApp Business API access

### Local Development
1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/renttrack.git
   cd renttrack
   ```

2. Create and activate virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run migrations
   ```bash
   python manage.py migrate
   ```

6. Start development server
   ```bash
   python manage.py runserver
   ```

7. For WhatsApp integration testing, use ngrok to expose your local server
   ```bash
   ngrok http 8000
   ```

## Deployment

The application is deployed on Render with the following configuration:

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure the environment variables
4. Set the build command: `pip install -r requirements.txt && python manage.py migrate`
5. Set the start command: `gunicorn your_project.wsgi:application`

## Security Considerations

- WhatsApp messages are encrypted but stored in the database
- Session timeouts after 10 minutes of inactivity
- Authentication through WhatsApp number verification
- Custom webhook URL for added security

## Future Enhancements

- Web portal for landlords with advanced reporting
- Mobile app for enhanced user experience
- Integration with payment processors
- Multi-language support
- Tenant-to-tenant communication features

## Contributing

We welcome contributions to RentTrack! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For support or inquiries:
- WhatsApp: +237 698 827 753

# Sodisys Kindergarten Tracker for Home Assistant

> **⚠️ IMPORTANT DISCLAIMERS:**
> 
> - **AI-Generated Code**: This project was created using AI assistance and may contain bugs, inefficiencies, or security issues
> - **Early Development Stage**: This integration is in early development and should be considered **experimental**
> - **Not Production Ready**: Use at your own risk - thoroughly test before relying on this integration for important automations
> - **No Official Support**: This is an unofficial integration not affiliated with Sodisys
> - **Data Privacy**: Review the code before use - ensure you're comfortable with how your data is handled

A custom Home Assistant integration that tracks kindergarten check-in/check-out data from Sodisys systems and presents children as device trackers.

## Features

- Creates device tracker entities for each child in your Sodisys account
- Shows children in kindergarten zone when checked in, "not_home" when checked out
- Provides check-in and check-out time sensors for each child
- Configurable timezone and update intervals

## Prerequisites

- Home Assistant 2022.7.0 or later
- Valid Sodisys account credentials

## Installation

### Method 1: HACS (Recommended when available)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL
6. Select "Integration" as the category
7. Click "Add"
8. Search for "Sodisys Kindergarten Tracker" and install

### Method 2: Manual Installation

1. Download or clone this repository
2. Copy the `custom_components/sodisys` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

> **Note**: This integration is configured entirely through the Home Assistant UI. No YAML configuration is supported.

1. Go to Home Assistant Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Sodisys Kindergarten Tracker"
4. Enter your configuration:
   - **Username**: Your Sodisys login username
   - **Password**: Your Sodisys login password
   - **Kindergarten Zone Name**: The name of the Home Assistant zone representing your kindergarten (default: "kindergarten")
   - **Kindergarten Timezone**: The timezone of your kindergarten for accurate timestamp conversion (default: "Europe/Berlin")
   - **Update Interval**: How often to check for updates in seconds (default: 300 seconds / 5 minutes)

## Setup Home Assistant Zone

Create a zone in Home Assistant that represents your kindergarten:

1. Go to Home Assistant Settings → Areas & zones
2. Click "Add Zone"
3. Configure the zone:
   - **Name**: Use the same name you configured in the integration (default: "kindergarten")
   - **Location**: Set the GPS coordinates of your kindergarten
   - **Radius**: Set an appropriate radius in meters

## License

This project is licensed under the European Union Public Licence v. 1.2 (EUPL-1.2) - see the LICENSE file for details.

## Support

⚠️ **This is experimental software with no guarantees of support or reliability.**

If you encounter issues:

1. Check the Home Assistant logs for errors
2. Verify your Sodisys credentials and zone configuration  
3. Open an issue on GitHub with relevant log entries
4. **Remember**: This is early-stage software - bugs and issues are expected
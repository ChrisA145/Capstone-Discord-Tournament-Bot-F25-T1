# Toxicity Tracking System

This document describes the implementation of the toxicity tracking system for the KSU Esports Tournament.

## Overview

The toxicity tracking system allows administrators to monitor and track player behavior by assigning "toxicity points" to players who demonstrate poor sportsmanship or violate community guidelines.

## Database Implementation

The system stores toxicity points in the `player` table with the following field:
- `toxicity_points`: An integer field defaulting to 0, incremented when admins report toxic behavior

## Commands

### Add Toxicity Point

Administrators can add a toxicity point to a player using this command:

```
/toxicity [player]
```

Where:
- `player`: The game name of the player to add a toxicity point to (required)

Example:
```
/toxicity RiftRager123
```

This will add 1 point to RiftRager123's toxicity score.

### View Toxicity Points

Anyone can check a player's toxicity score using:

```
/get_toxicity [player]
```

Where:
- `player`: The game name of the player to check (required)

Example:
```
/get_toxicity RiftRager123
```

This will display the current number of toxicity points for the specified player.

## Permissions

- Only server administrators (users with the Administrator permission) can add toxicity points
- Anyone can view a player's toxicity points

## Implementation Details

- The system uses a case-insensitive search to find players by name
- Commands provide immediate feedback on success or failure
- All commands have ephemeral responses (only visible to the command user)
- Error handling is implemented to prevent crashes if a player isn't found

## Future Enhancements

Potential future enhancements could include:
- Automatic role assignment based on toxicity levels
- Decay of toxicity points over time
- Reporting system for players to report toxic behavior
- Admin panel to review and manage toxicity reports
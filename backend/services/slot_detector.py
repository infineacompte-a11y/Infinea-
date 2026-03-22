"""
Slot Detector Service for InFinea.
Analyzes calendar events to detect free time slots suitable for micro-actions.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)

# Default slot detection settings
DEFAULT_SETTINGS = {
    'slot_detection_enabled': True,
    'min_slot_duration': 5,  # minutes
    'max_slot_duration': 20,  # minutes
    'detection_window_start': '09:00',
    'detection_window_end': '18:00',
    'excluded_keywords': ['focus', 'deep work', 'lunch', 'break', 'busy', 'blocked'],
    'advance_notification_minutes': 5,
    'preferred_categories_by_time': {
        'morning': 'learning',      # 06:00-12:00
        'afternoon': 'productivity', # 12:00-17:00
        'evening': 'well_being'      # 17:00-22:00
    }
}


def parse_time(time_str: str) -> tuple:
    """Parse time string HH:MM to (hour, minute) tuple."""
    parts = time_str.split(':')
    return int(parts[0]), int(parts[1])


def is_within_detection_window(dt: datetime, settings: Dict) -> bool:
    """Check if datetime is within the configured detection window."""
    start_h, start_m = parse_time(settings.get('detection_window_start', '09:00'))
    end_h, end_m = parse_time(settings.get('detection_window_end', '18:00'))
    
    dt_minutes = dt.hour * 60 + dt.minute
    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m
    
    return start_minutes <= dt_minutes <= end_minutes


def event_has_excluded_keyword(event: Dict, keywords: List[str]) -> bool:
    """Check if event title/description contains excluded keywords."""
    title = (event.get('summary') or '').lower()
    description = (event.get('description') or '').lower()
    
    for keyword in keywords:
        if keyword.lower() in title or keyword.lower() in description:
            return True
    return False


def get_event_times(event: Dict) -> tuple:
    """Extract start and end times from a calendar event."""
    start = event.get('start', {})
    end = event.get('end', {})
    
    # Handle all-day events
    if 'date' in start:
        return None, None  # Skip all-day events
    
    start_str = start.get('dateTime')
    end_str = end.get('dateTime')
    
    if not start_str or not end_str:
        return None, None
    
    # Parse ISO datetime
    start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
    
    return start_dt, end_dt


def get_category_for_time(dt: datetime, preferences: Dict) -> str:
    """Determine the appropriate category based on time of day."""
    hour = dt.hour
    categories = preferences.get('preferred_categories_by_time', DEFAULT_SETTINGS['preferred_categories_by_time'])
    
    if 6 <= hour < 12:
        return categories.get('morning', 'learning')
    elif 12 <= hour < 17:
        return categories.get('afternoon', 'productivity')
    else:
        return categories.get('evening', 'well_being')


async def detect_free_slots(
    events: List[Dict],
    settings: Dict,
    user_timezone: str = 'UTC'
) -> List[Dict]:
    """
    Detect free time slots between calendar events.
    
    Args:
        events: List of calendar events (sorted by start time)
        settings: User's slot detection settings
        user_timezone: User's timezone
    
    Returns:
        List of detected free slots with suggested actions
    """
    if not settings.get('slot_detection_enabled', True):
        return []
    
    min_duration = settings.get('min_slot_duration', DEFAULT_SETTINGS['min_slot_duration'])
    max_duration = settings.get('max_slot_duration', DEFAULT_SETTINGS['max_slot_duration'])
    excluded_keywords = settings.get('excluded_keywords', DEFAULT_SETTINGS['excluded_keywords'])
    
    free_slots = []
    now = datetime.now(timezone.utc)
    
    # Filter out events with excluded keywords and get valid event times
    valid_events = []
    for event in events:
        if event_has_excluded_keyword(event, excluded_keywords):
            continue
        
        start_dt, end_dt = get_event_times(event)
        if start_dt and end_dt:
            valid_events.append({
                'start': start_dt,
                'end': end_dt,
                'summary': event.get('summary', 'Event')
            })
    
    # Sort by start time
    valid_events.sort(key=lambda x: x['start'])
    
    # Detect gaps between events
    for i in range(len(valid_events)):
        if i == 0:
            # Check gap from now to first event
            gap_start = now
            gap_end = valid_events[i]['start']
        else:
            # Check gap between current and previous event
            gap_start = valid_events[i - 1]['end']
            gap_end = valid_events[i]['start']
        
        # Skip if gap is in the past
        if gap_end <= now:
            continue
        
        # Adjust gap_start if it's in the past
        if gap_start < now:
            gap_start = now
        
        # Check if within detection window
        if not is_within_detection_window(gap_start, settings):
            continue
        
        # Calculate gap duration
        gap_duration = int((gap_end - gap_start).total_seconds() / 60)
        
        # Check if gap is within acceptable range
        if min_duration <= gap_duration <= max_duration:
            slot = {
                'slot_id': f"slot_{uuid.uuid4().hex[:12]}",
                'start_time': gap_start.isoformat(),
                'end_time': gap_end.isoformat(),
                'duration_minutes': gap_duration,
                'suggested_category': get_category_for_time(gap_start, settings),
                'notification_sent': False,
                'action_taken': False,
                'created_at': now.isoformat()
            }
            free_slots.append(slot)
    
    # Check gap after last event until end of detection window
    if valid_events:
        last_event_end = valid_events[-1]['end']
        if last_event_end > now and is_within_detection_window(last_event_end, settings):
            end_h, end_m = parse_time(settings.get('detection_window_end', '18:00'))
            window_end = last_event_end.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
            
            if window_end > last_event_end:
                gap_duration = int((window_end - last_event_end).total_seconds() / 60)
                
                if min_duration <= gap_duration <= max_duration:
                    slot = {
                        'slot_id': f"slot_{uuid.uuid4().hex[:12]}",
                        'start_time': last_event_end.isoformat(),
                        'end_time': window_end.isoformat(),
                        'duration_minutes': gap_duration,
                        'suggested_category': get_category_for_time(last_event_end, settings),
                        'notification_sent': False,
                        'action_taken': False,
                        'created_at': now.isoformat()
                    }
                    free_slots.append(slot)
    
    return free_slots


async def match_action_to_slot(
    slot: Dict,
    available_actions: List[Dict],
    user_subscription: str = 'free'
) -> Optional[Dict]:
    """
    Find the best micro-action for a given slot.
    
    Args:
        slot: The free slot details
        available_actions: List of available micro-actions
        user_subscription: User's subscription tier
    
    Returns:
        Best matching action or None
    """
    duration = slot['duration_minutes']
    category = slot['suggested_category']
    
    # Filter actions by subscription
    if user_subscription == 'free':
        available_actions = [a for a in available_actions if not a.get('is_premium', False)]
    
    # Find actions that fit the duration and match category
    matching_actions = []
    for action in available_actions:
        if action['duration_min'] <= duration and action.get('category') == category:
            matching_actions.append(action)
    
    # If no category match, find any action that fits
    if not matching_actions:
        for action in available_actions:
            if action['duration_min'] <= duration:
                matching_actions.append(action)
    
    # Return the best match (prefer actions closer to slot duration)
    if matching_actions:
        matching_actions.sort(key=lambda a: abs(a['duration_min'] - duration))
        return matching_actions[0]
    
    return None

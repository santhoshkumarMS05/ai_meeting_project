from playwright.sync_api import sync_playwright
import time
import threading
import requests
import uuid

def setup_and_join(page):
    """Reusable function to setup mic/camera and join meeting"""
    print("🔧 Setting up meeting preferences...")
    time.sleep(3)
    
    # Auto-fill name as "Luffy"
    try:
        name_input = page.locator('input[placeholder*="name" i], input[aria-label*="name" i], input[type="text"]').first
        if name_input.is_visible(timeout=5000):
            name_input.fill("Luffy")
            print("✅ Name auto-filled as 'Luffy'")
            time.sleep(1)
    except Exception as e:
        print(f"⚠️ Name input not found: {e}")
    
    # Turn off microphone
    try:
        mic_button = page.locator('button[aria-label*="microphone" i], button[aria-label*="Turn off microphone" i], div[aria-label*="Turn off microphone" i]').first
        if mic_button.is_visible(timeout=5000):
            mic_button.click()
            print("🎤 Microphone turned OFF")
            time.sleep(1)
    except Exception as e:
        print(f"⚠️ Microphone button not found or already off: {e}")
    
    # Turn off camera
    try:
        camera_button = page.locator('button[aria-label*="camera" i], button[aria-label*="Turn off camera" i], div[aria-label*="Turn off camera" i]').first
        if camera_button.is_visible(timeout=5000):
            camera_button.click()
            print("📷 Camera turned OFF")
            time.sleep(1)
    except Exception as e:
        print(f"⚠️ Camera button not found or already off: {e}")
    
    time.sleep(2)
    
    # Click "Ask to join" or "Join now"
    try:
        join_selectors = [
            'button:has-text("Ask to join")',
            'button:has-text("Join now")',
            'button:has-text("Join")',
            'span:has-text("Ask to join")',
            'span:has-text("Join now")'
        ]
        
        joined = False
        for selector in join_selectors:
            try:
                join_button = page.locator(selector).first
                if join_button.is_visible(timeout=3000):
                    join_button.click()
                    print("✅ Clicked 'Ask to join' / 'Join now' button")
                    joined = True
                    break
            except:
                continue
        
        if not joined:
            print("⚠️ Join button not found, might be auto-joined")
    
    except Exception as e:
        print(f"⚠️ Join button error: {e}")
    
    print("✅ Setup complete - Bot is in the meeting")


def check_if_alone_in_meeting(page):
    """Check if bot is alone in the meeting"""
    try:
        # Check for participant count or "You're the only one here" message
        alone_indicators = [
            'text="You\'re the only one here"',
            'text="No one else is here"',
            '[data-participant-count="1"]'
        ]
        
        for indicator in alone_indicators:
            try:
                if page.locator(indicator).is_visible(timeout=2000):
                    return True
            except:
                continue
        
        # Check participant count in the UI
        try:
            participants = page.locator('[aria-label*="participant" i], [data-number-of-participants]').first
            if participants.is_visible(timeout=2000):
                text = participants.inner_text().lower()
                if "1" in text or "only you" in text:
                    return True
        except:
            pass
            
        return False
        
    except Exception as e:
        print(f"⚠️ Error checking participants: {e}")
        return False


def check_if_meeting_has_participants(page):
    """Check if there are any participants in the meeting (even from rejoin screen)"""
    try:
        # Try to check participant count from the main meeting interface
        participant_indicators = [
            '[data-number-of-participants]',
            '[aria-label*="participant" i]',
            'button[aria-label*="Show everyone" i]'
        ]
        
        for indicator in participant_indicators:
            try:
                element = page.locator(indicator).first
                if element.is_visible(timeout=2000):
                    text = element.inner_text().lower()
                    # If it shows more than 1 or contains numbers > 1
                    if any(str(i) in text for i in range(2, 100)):
                        return True
            except:
                continue
        
        # Also check the page for any indication of active meeting
        active_meeting_indicators = [
            'text="in this call"',
            'text="joined"',
            '[data-meeting-active="true"]'
        ]
        
        for indicator in active_meeting_indicators:
            try:
                if page.locator(indicator).is_visible(timeout=1000):
                    return True
            except:
                continue
                
        return False
        
    except Exception as e:
        print(f"⚠️ Error checking meeting participants: {e}")
        return False


def stop_recording_and_process(meeting_id):
    """Helper function to stop recording and process meeting"""
    try:
        print("🛑 Stopping recording...")
        response = requests.post('http://127.0.0.1:5000/meeting/stop', 
                                json={'meeting_id': meeting_id}, timeout=10)
        if response.status_code == 200:
            print("✅ Recording stopped successfully")
        else:
            print(f"⚠️ Failed to stop recording: {response.text}")
    except Exception as e:
        print(f"❌ Error stopping recording: {e}")
    
    try:
        print("🔄 Starting meeting processing...")
        response = requests.post('http://127.0.0.1:5000/meeting/process', 
                                json={'meeting_id': meeting_id}, timeout=30)
        if response.status_code == 200:
            print("✅ Meeting processing started successfully")
        else:
            print(f"⚠️ Failed to process meeting: {response.text}")
    except Exception as e:
        print(f"❌ Error processing meeting: {e}")


def leave_meeting(page, meeting_id):
    """Function to leave the meeting and trigger backend stop/process"""
    try:
        # Click the leave/end call button
        leave_selectors = [
            'button[aria-label*="Leave call" i]',
            'button[aria-label*="End call" i]',
            '[data-call-ended-button]',
            'button:has-text("Leave call")'
        ]
        
        for selector in leave_selectors:
            try:
                leave_button = page.locator(selector).first
                if leave_button.is_visible(timeout=3000):
                    leave_button.click()
                    print("📞 Left the meeting")
                    
                    # Stop recording and process
                    stop_recording_and_process(meeting_id)
                    
                    return True
            except:
                continue
        
        print("⚠️ Could not find leave button")
        return False
        
    except Exception as e:
        print(f"⚠️ Error leaving meeting: {e}")
        return False


def monitor_and_handle_rejoin(page, meeting_id, recording_started):
    """Monitor meeting and handle auto-rejoin with participant check"""
    rejoin_selectors = [
        'button:has-text("Rejoin")',
        'span:has-text("Rejoin")',
        '[aria-label*="Rejoin" i]'
    ]
    
    # Selectors to detect if meeting has ended
    meeting_ended_selectors = [
        'text="You left the meeting"',
        'text="Meeting ended"',
        'text="You\'ve been removed from the meeting"',
        'text="Return to home screen"',
        'button:has-text("Return to home screen")',
        'text="Your meeting has ended"',
        'text="Thanks for joining"'
    ]
    
    alone_start_time = None
    
    while True:
        try:
            # Check if we're still on a meet.google.com page
            if "meet.google.com" not in page.url:
                print("❌ Left Google Meet completely")
                
                # Stop recording if still active
                if recording_started:
                    stop_recording_and_process(meeting_id)
                break
            
            # Check if meeting has ended (PRIORITY CHECK)
            meeting_ended = False
            for selector in meeting_ended_selectors:
                try:
                    if page.locator(selector).is_visible(timeout=1000):
                        print(f"🛑 Meeting ended detected: '{selector}'")
                        meeting_ended = True
                        break
                except:
                    continue
            
            if meeting_ended:
                if recording_started:
                    stop_recording_and_process(meeting_id)
                print("✅ Meeting session completed - Recording stopped")
                return  # Exit monitoring loop
            
            # Check for rejoin button
            rejoin_detected = False
            for selector in rejoin_selectors:
                try:
                    rejoin_button = page.locator(selector).first
                    if rejoin_button.is_visible(timeout=2000):
                        rejoin_text = rejoin_button.inner_text()
                        if "Rejoin" in rejoin_text or "rejoin" in rejoin_text.lower():
                            rejoin_detected = True
                            
                            # Check if there are participants in the meeting
                            has_participants = check_if_meeting_has_participants(page)
                            
                            if has_participants:
                                print("🔄 Rejoin button detected and participants are in meeting! Auto-rejoining...")
                                rejoin_button.click()
                                time.sleep(2)
                                
                                # Run the setup again
                                setup_and_join(page)
                                print("🔄 Successfully rejoined the meeting")
                                alone_start_time = None  # Reset alone timer
                            else:
                                print("⏹️ Rejoin button detected but no participants in meeting. Not rejoining.")
                                
                                # Stop recording and process
                                if recording_started:
                                    stop_recording_and_process(meeting_id)
                                return  # Exit - don't rejoin empty meeting
                            break
                except:
                    continue
            
            # If rejoin was detected and handled, skip participant check for this iteration
            if rejoin_detected:
                time.sleep(5)
                continue
            
            # Check if bot is alone in meeting (only when actively in meeting)
            is_alone = check_if_alone_in_meeting(page)
            
            if is_alone:
                if alone_start_time is None:
                    alone_start_time = time.time()
                    print("⚠️ Bot is alone in the meeting. Will leave in 30 seconds if no one joins...")
                else:
                    time_alone = time.time() - alone_start_time
                    if time_alone >= 30:  # 30 seconds
                        print("❌ No one joined for 30 seconds. Leaving meeting...")
                        leave_meeting(page, meeting_id)
                        time.sleep(2)
                        # After leaving, continue monitoring for rejoin
                        alone_start_time = None
                    else:
                        remaining = 30 - int(time_alone)
                        print(f"⏳ Alone for {int(time_alone)}s. Leaving in {remaining}s if no one joins...")
            else:
                if alone_start_time is not None:
                    print("✅ Someone joined! Timer reset. Continuing meeting...")
                alone_start_time = None  # Reset timer when someone is present
            
            # Sleep for a bit before checking again
            time.sleep(5)
            
        except Exception as e:
            print(f"⚠️ Monitoring error: {e}")
            time.sleep(5)


def join_meeting_background(meet_link: str, meeting_id: str, user_email: str):
    """Background function that actually joins the meeting"""
    recording_started = False
    
    # Add https:// if not present
    if not meet_link.startswith('http'):
        meet_link = 'https://' + meet_link
    
    with sync_playwright() as p:
        # Launch browser without user profile - works for all users
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream"
            ]
        )
        
        context = browser.new_context(
            permissions=["camera", "microphone"]
        )
        
        page = context.new_page()
        
        try:
            page.goto(meet_link, timeout=60000)
        except Exception as e:
            print(f"❌ Error loading meeting link: {e}")
            browser.close()
            return
        
        print("✅ Loaded Google Meet page")
        
        # Initial setup and join
        setup_and_join(page)
        
        print("⏳ Waiting for host to admit...")
        
        # Wait a bit for meeting to fully load
        time.sleep(5)
        
        # Start recording after joining - use backend's meeting_id
        try:
            response = requests.post('http://127.0.0.1:5000/meeting/start', 
                                    json={
                                        'meeting_title': 'Auto Meeting',
                                        'user_email': user_email
                                    }, 
                                    timeout=10)
            if response.status_code == 200:
                result = response.json()
                meeting_id = result['meeting_id']  # Use backend's meeting_id
                recording_started = True
                print(f"🔍 Meeting ID: {meeting_id}")
                print(f"👤 User Email: {user_email}")
                print(f"🔴 Recording started successfully")
            else:
                print(f"⚠️ Failed to start recording: {response.text}")
        except Exception as e:
            print(f"❌ Error starting recording: {e}")
        
        print("🤖 Bot 'Luffy' is now in the meeting")
        print("🔄 Smart Auto-rejoin is ENABLED")
        print("⏰ Bot will leave after 30 seconds if alone")
        print("🎯 Bot will auto-rejoin ONLY if participants are present in the meeting")
        print("🛑 Bot will auto-stop recording when meeting ends")
        
        try:
            # Monitor indefinitely until conditions met
            monitor_and_handle_rejoin(page, meeting_id, recording_started)
                    
        except Exception as e:
            print(f"❌ Error in meeting loop: {e}")
            
            # Ensure recording is stopped on error
            if recording_started:
                stop_recording_and_process(meeting_id)
                print("✅ Recording stopped and processing initiated (error cleanup)")
        
        print("✅ Meeting session completed")
        browser.close()


def join_meeting(meet_link: str, user_email: str):
    """Main function called by Flask - starts meeting in background thread with backend integration"""
    
    print("🚀 Starting meeting bot with automatic recording...")
    print(f"👤 User: {user_email}")
    
    # meeting_id will be assigned by backend after /meeting/start
    thread = threading.Thread(target=join_meeting_background, args=(meet_link, None, user_email))
    thread.daemon = True  # Thread will close when main program closes
    thread.start()
    
    # Return immediately so Flask can respond
    return {"status": "joined"}
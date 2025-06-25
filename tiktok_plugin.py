import sys
import json
import asyncio
import threading
import re
import requests
import logging
from datetime import datetime
from collections import defaultdict

# Configuration du logging pour debug
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from TikTokLive import TikTokLiveClient
    from TikTokLive.events import (
        ConnectEvent, CommentEvent, GiftEvent,
        DiggEvent, LikeEvent, RoomUserSeqEvent,
        FollowEvent, ShareEvent, QuestionNewEvent,
        JoinEvent, LiveEndEvent
    )
    TIKTOK_AVAILABLE = True
except ImportError:
    TIKTOK_AVAILABLE = False
    logging.error("TikTokLive module not available")

class TikTokLivePlugin:
    def __init__(self):
        self.client = None
        self.monitoring = False
        self.current_username = ""
        self.total_likes = 0
        self.user_likes = defaultdict(int)
        self.initial_followers = 0
        self.loop = None
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
    def send_tp_message(self, message_type, data=None):
        """Envoie un message à TouchPortal"""
        try:
            message = {"type": message_type}
            if data:
                message.update(data)
            print(json.dumps(message), flush=True)
        except Exception as e:
            logging.error(f"Error sending TP message: {e}")
    
    def update_state(self, state_id, value):
        """Met à jour un état TouchPortal"""
        try:
            self.send_tp_message("stateUpdate", {
                "id": state_id,
                "value": str(value)
            })
        except Exception as e:
            logging.error(f"Error updating state {state_id}: {e}")
    
    def trigger_event(self, event_id, data=None):
        """Déclenche un événement TouchPortal"""
        try:
            message = {"type": "broadcast", "event": event_id}
            if data:
                message.update(data)
            print(json.dumps(message), flush=True)
        except Exception as e:
            logging.error(f"Error triggering event {event_id}: {e}")

    def fetch_tiktok_followers(self, username: str) -> int:
        """Récupère le nombre de followers"""
        try:
            url = f"https://www.tiktok.com/@{username}"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            match = re.search(r'"followerCount":(\d+)', resp.text)
            return int(match.group(1)) if match else 0
        except Exception as e:
            logging.error(f"Error fetching followers for {username}: {e}")
            return 0

    async def start_monitoring(self, username):
        """Démarre le monitoring d'un utilisateur TikTok"""
        try:
            if not TIKTOK_AVAILABLE:
                self.update_state("tiktok.live.status", "Error: TikTokLive not installed")
                return
                
            if self.monitoring:
                await self.stop_monitoring()
            
            self.current_username = username.lstrip('@').strip()
            if not self.current_username:
                self.update_state("tiktok.live.status", "Error: Invalid username")
                return
                
            self.client = TikTokLiveClient(unique_id=self.current_username)
            self.total_likes = 0
            self.user_likes.clear()
            self.initial_followers = self.fetch_tiktok_followers(self.current_username)
            
            # Configuration des événements
            self.setup_event_handlers()
            
            self.monitoring = True
            self.update_state("tiktok.live.status", "Connecting...")
            self.update_state("tiktok.live.current_username", self.current_username)
            self.update_state("tiktok.live.followers", self.initial_followers)
            
            await self.client.start()
            
        except Exception as e:
            logging.error(f"Error starting monitoring: {e}")
            self.monitoring = False
            self.update_state("tiktok.live.status", f"Error: {str(e)[:50]}")

    async def stop_monitoring(self):
        """Arrête le monitoring"""
        try:
            if self.client and self.monitoring:
                await self.client.stop()
        except Exception as e:
            logging.error(f"Error stopping monitoring: {e}")
        finally:
            self.monitoring = False
            self.update_state("tiktok.live.status", "Stopped")
            self.reset_states()

    def setup_event_handlers(self):
        """Configure les gestionnaires d'événements TikTok"""
        if not self.client or not TIKTOK_AVAILABLE:
            return
            
        try:
            @self.client.on(ConnectEvent)
            async def on_connect(event):
                try:
                    self.update_state("tiktok.live.status", "Connected")
                    if hasattr(self.client, 'room_id'):
                        self.update_state("tiktok.live.room_id", str(self.client.room_id))
                    self.trigger_event("tiktok.live.connected")
                except Exception as e:
                    logging.error(f"Error in on_connect: {e}")

            @self.client.on(CommentEvent)
            async def on_comment(event):
                try:
                    comment = getattr(event, 'comment', '')
                    username = getattr(getattr(event, 'user', None), 'nickname', 'Unknown')
                    
                    self.update_state("tiktok.live.last_comment", comment)
                    self.update_state("tiktok.live.last_commenter", username)
                    self.trigger_event("tiktok.live.new_comment")
                except Exception as e:
                    logging.error(f"Error in on_comment: {e}")

            @self.client.on(GiftEvent)
            async def on_gift(event):
                try:
                    gift = getattr(event, 'gift', None)
                    if not gift:
                        return
                        
                    count = getattr(gift, 'repeat_count', getattr(gift, 'repeatCount', 1)) or 1
                    name = getattr(gift, 'name', getattr(gift, 'giftName', 'Unknown Gift'))
                    value = getattr(gift, 'diamond_count', 0) * count
                    sender = getattr(getattr(event, 'user', None), 'nickname', 'Unknown')
                    
                    self.trigger_event("tiktok.live.gift_received")
                    self.update_state("tiktok.live.last_commenter", sender)
                except Exception as e:
                    logging.error(f"Error in on_gift: {e}")

            @self.client.on(DiggEvent)
            async def on_digg(event):
                try:
                    count = getattr(event, 'digg_count', getattr(event, 'diggCount', 1)) or 1
                    user_id = getattr(getattr(event, 'user', None), 'unique_id', 'unknown')
                    
                    self.total_likes += count
                    self.user_likes[user_id] += count
                    self.update_state("tiktok.live.total_likes", self.total_likes)
                except Exception as e:
                    logging.error(f"Error in on_digg: {e}")

            @self.client.on(LikeEvent)
            async def on_like(event):
                try:
                    user_id = getattr(getattr(event, 'user', None), 'unique_id', 'unknown')
                    self.total_likes += 1
                    self.user_likes[user_id] += 1
                    self.update_state("tiktok.live.total_likes", self.total_likes)
                except Exception as e:
                    logging.error(f"Error in on_like: {e}")

            @self.client.on(RoomUserSeqEvent)
            async def on_viewers(event):
                try:
                    viewers = getattr(event, 'total_user', 0)
                    self.update_state("tiktok.live.viewers", viewers)
                    
                    # Mise à jour périodique des followers
                    current_followers = self.fetch_tiktok_followers(self.current_username)
                    self.update_state("tiktok.live.followers", current_followers)
                except Exception as e:
                    logging.error(f"Error in on_viewers: {e}")

            @self.client.on(FollowEvent)
            async def on_follow(event):
                try:
                    follower = getattr(getattr(event, 'user', None), 'nickname', 'Unknown')
                    self.trigger_event("tiktok.live.new_follower")
                except Exception as e:
                    logging.error(f"Error in on_follow: {e}")

            @self.client.on(LiveEndEvent)
            async def on_end(event):
                try:
                    final_followers = self.fetch_tiktok_followers(self.current_username)
                    self.update_state("tiktok.live.followers", final_followers)
                    self.update_state("tiktok.live.status", "Stream Ended")
                    self.trigger_event("tiktok.live.stream_ended")
                    self.monitoring = False
                except Exception as e:
                    logging.error(f"Error in on_end: {e}")
                    
        except Exception as e:
            logging.error(f"Error setting up event handlers: {e}")

    def reset_states(self):
        """Remet à zéro tous les états"""
        try:
            self.update_state("tiktok.live.current_username", "")
            self.update_state("tiktok.live.viewers", "0")
            self.update_state("tiktok.live.total_likes", "0")
            self.update_state("tiktok.live.followers", "0")
            self.update_state("tiktok.live.last_comment", "")
            self.update_state("tiktok.live.last_commenter", "")
            self.update_state("tiktok.live.room_id", "")
        except Exception as e:
            logging.error(f"Error resetting states: {e}")

    def run_async_in_thread(self, coro):
        """Exécute une coroutine dans un thread séparé"""
        def run_in_thread():
            try:
                if self.loop is None or self.loop.is_closed():
                    self.loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self.loop)
                self.loop.run_until_complete(coro)
            except Exception as e:
                logging.error(f"Error in async thread: {e}")
        
        try:
            if self.monitor_thread and self.monitor_thread.is_alive():
                # Arrêter le thread précédent proprement
                self.stop_event.set()
                if self.loop and not self.loop.is_closed():
                    try:
                        future = asyncio.run_coroutine_threadsafe(self.stop_monitoring(), self.loop)
                        future.result(timeout=5)
                    except Exception as e:
                        logging.error(f"Error stopping previous thread: {e}")
            
            self.stop_event.clear()
            self.monitor_thread = threading.Thread(target=run_in_thread, daemon=True)
            self.monitor_thread.start()
        except Exception as e:
            logging.error(f"Error starting async thread: {e}")

    def handle_tp_message(self, message):
        """Traite les messages reçus de TouchPortal"""
        try:
            msg_type = message.get("type")
            
            if msg_type == "info":
                # TouchPortal demande des informations sur le plugin
                self.send_tp_message("info", {
                    "sdkVersion": 6,
                    "version": "1.0.0",
                    "plugin": "TikTok Live Monitor"
                })
                
            elif msg_type == "settings":
                # Initialisation des états
                self.reset_states()
                self.update_state("tiktok.live.status", "Ready" if TIKTOK_AVAILABLE else "TikTokLive not installed")
                
            elif msg_type == "action":
                action_id = message.get("actionId")
                
                if action_id == "tiktok.live.start":
                    if not TIKTOK_AVAILABLE:
                        self.update_state("tiktok.live.status", "Error: TikTokLive not installed")
                        return
                        
                    data = message.get("data", [])
                    username = ""
                    for item in data:
                        if item.get("id") == "tiktok.live.username":
                            username = item.get("value", "").strip()
                            break
                    
                    if username:
                        self.run_async_in_thread(self.start_monitoring(username))
                    else:
                        self.update_state("tiktok.live.status", "Error: No username provided")
                        
                elif action_id == "tiktok.live.stop":
                    self.run_async_in_thread(self.stop_monitoring())
                    
        except Exception as e:
            logging.error(f"Error handling TP message: {e}")
            self.send_tp_message("error", {"message": f"Plugin error: {str(e)[:100]}"})

    def run(self):
        """Boucle principale du plugin"""
        try:
            # Envoyer un message de démarrage
            self.send_tp_message("info", {
                "sdkVersion": 6,
                "version": "1.0.0",
                "plugin": "TikTok Live Monitor"
            })
            
            while True:
                try:
                    line = sys.stdin.readline()
                    if not line:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                        
                    message = json.loads(line)
                    self.handle_tp_message(message)
                    
                except json.JSONDecodeError as e:
                    logging.error(f"JSON decode error: {e}")
                    continue
                except EOFError:
                    break
                except Exception as e:
                    logging.error(f"Error in main loop: {e}")
                    continue
                    
        except KeyboardInterrupt:
            logging.info("Plugin interrupted by user")
        except Exception as e:
            logging.error(f"Fatal error in plugin: {e}")
        finally:
            try:
                if self.monitoring:
                    # Arrêt propre
                    self.stop_event.set()
                    if self.loop and not self.loop.is_closed():
                        try:
                            future = asyncio.run_coroutine_threadsafe(self.stop_monitoring(), self.loop)
                            future.result(timeout=5)
                        except:
                            pass
            except Exception as e:
                logging.error(f"Error in cleanup: {e}")

def main():
    try:
        plugin = TikTokLivePlugin()
        plugin.run()
    except Exception as e:
        logging.error(f"Fatal error starting plugin: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
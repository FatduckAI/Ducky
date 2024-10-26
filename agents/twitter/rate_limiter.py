import logging
import random
import time
from datetime import datetime, timedelta
from functools import wraps


class TwitterRateLimiter:
    def __init__(self):
        self.post_tweet_requests = []  # 300 per 3 hours -> buffer to 200
        self.search_requests = []      # 180 per 15 min -> buffer to 120
        self.user_lookup_requests = [] # 900 per 15 min -> buffer to 600
        
        self.window_size = {
            'post_tweet': 3 * 60 * 60,  # 3 hours
            'search': 15 * 60,          # 15 minutes
            'user_lookup': 15 * 60      # 15 minutes
        }
        
        self.limits = {
            'post_tweet': {
                'actual_limit': 300,
                'buffer_limit': 200,  # Using ~66% of actual limit
                'min_interval': (3 * 60 * 60) / 200,  # Minimum time between requests
                'jitter_range': (5, 15)  # Random delay between 5-15 seconds
            },
            'search': {
                'actual_limit': 180,
                'buffer_limit': 120,  # Using ~66% of actual limit
                'min_interval': (15 * 60) / 120,  # Minimum time between requests
                'jitter_range': (2, 8)   # Random delay between 2-8 seconds
            },
            'user_lookup': {
                'actual_limit': 900,
                'buffer_limit': 600,  # Using ~66% of actual limit
                'min_interval': (15 * 60) / 600,  # Minimum time between requests
                'jitter_range': (1, 5)   # Random delay between 1-5 seconds
            }
        }
        
        # Track consecutive errors
        self.consecutive_errors = 0
        self.max_consecutive_errors = 3
        self.backoff_base = 60  # Base backoff time in seconds
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def _apply_exponential_backoff(self):
        """Apply exponential backoff when consecutive errors occur"""
        if self.consecutive_errors >= self.max_consecutive_errors:
            backoff_time = self.backoff_base * (2 ** (self.consecutive_errors - self.max_consecutive_errors))
            backoff_time = min(backoff_time, 3600)  # Cap at 1 hour
            logging.warning(f"Applying exponential backoff: sleeping for {backoff_time} seconds")
            time.sleep(backoff_time)
    
    def _clean_old_requests(self, requests_list, endpoint_type):
        cutoff_time = datetime.now() - timedelta(seconds=self.window_size[endpoint_type])
        while requests_list and requests_list[0] < cutoff_time:
            requests_list.pop(0)
    
    def _add_jitter(self, endpoint_type):
        """Add random jitter to help prevent synchronized requests"""
        jitter_range = self.limits[endpoint_type]['jitter_range']
        jitter = random.uniform(jitter_range[0], jitter_range[1])
        if jitter > 0:
            logging.debug(f"Adding {jitter:.2f}s jitter delay for {endpoint_type}")
            time.sleep(jitter)
    
    def check_rate_limit(self, endpoint_type):
        if endpoint_type == 'post_tweet':
            requests_list = self.post_tweet_requests
        elif endpoint_type == 'search':
            requests_list = self.search_requests
        else:
            requests_list = self.user_lookup_requests
        
        self._clean_old_requests(requests_list, endpoint_type)
        self._apply_exponential_backoff()
        
        limit_config = self.limits[endpoint_type]
        buffer_limit = limit_config['buffer_limit']
        min_interval = limit_config['min_interval']
        
        # Calculate hourly and window-based limits
        window_limit = (buffer_limit * 3600) / self.window_size[endpoint_type]
        current_window_requests = len(requests_list)
        
        # Check if we're approaching limits
        if current_window_requests >= buffer_limit * 0.8:  # If we're at 80% of buffer
            sleep_time = self.window_size[endpoint_type] * 0.1  # Sleep for 10% of window
            logging.warning(f"Approaching rate limit for {endpoint_type}. "
                          f"Sleeping for {sleep_time:.2f} seconds. "
                          f"Current usage: {current_window_requests}/{buffer_limit}")
            time.sleep(sleep_time)
            self._clean_old_requests(requests_list, endpoint_type)
        
        # Enforce minimum interval with jitter
        if requests_list:
            time_since_last = (datetime.now() - requests_list[-1]).total_seconds()
            if time_since_last < min_interval:
                sleep_time = min_interval - time_since_last
                logging.info(f"Enforcing minimum interval for {endpoint_type}. "
                           f"Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        # Add jitter to help prevent synchronized requests
        self._add_jitter(endpoint_type)
        
        requests_list.append(datetime.now())

    def get_current_usage(self, endpoint_type):
        if endpoint_type == 'post_tweet':
            requests_list = self.post_tweet_requests
        elif endpoint_type == 'search':
            requests_list = self.search_requests
        else:
            requests_list = self.user_lookup_requests
            
        self._clean_old_requests(requests_list, endpoint_type)
        
        limit_config = self.limits[endpoint_type]
        window_limit = (limit_config['buffer_limit'] * 3600) / self.window_size[endpoint_type]
        
        return {
            'current_requests': len(requests_list),
            'buffer_limit': limit_config['buffer_limit'],
            'actual_limit': limit_config['actual_limit'],
            'window_limit': window_limit,
            'usage_percentage': (len(requests_list) / limit_config['buffer_limit']) * 100
        }

def rate_limit(endpoint_type):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                rate_limiter.check_rate_limit(endpoint_type)
                
                # Log usage every 5 requests
                usage = rate_limiter.get_current_usage(endpoint_type)
                if usage['current_requests'] % 5 == 0:
                    logging.info(
                        f"Rate limit status for {endpoint_type}: "
                        f"{usage['current_requests']}/{usage['buffer_limit']} "
                        f"({usage['usage_percentage']:.1f}%)"
                    )
                
                result = func(*args, **kwargs)
                rate_limiter.consecutive_errors = 0  # Reset on success
                return result
                
            except Exception as e:
                rate_limiter.consecutive_errors += 1
                logging.error(f"Error in rate-limited call: {str(e)}")
                raise
                
        return wrapper
    return decorator

rate_limiter = TwitterRateLimiter()
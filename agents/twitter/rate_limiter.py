# rate_limiter.py
import logging
import time
from datetime import datetime, timedelta
from functools import wraps


class TwitterRateLimiter:
    def __init__(self):
        self.post_tweet_requests = []  # 200 per 15 min -> buffer to 180
        self.search_requests = []      # 180 per 15 min -> buffer to 160
        
        self.window_size = 15 * 60
        
        self.limits = {
            'post_tweet': {
                'actual_limit': 200,
                'buffer_limit': 180,  # Using 90% of actual limit
                'min_interval': self.window_size / 180  # Minimum time between requests
            },
            'search': {
                'actual_limit': 180,
                'buffer_limit': 160,  # Using ~89% of actual limit
                'min_interval': self.window_size / 160  # Minimum time between requests
            }
        }
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def _clean_old_requests(self, requests_list):
        cutoff_time = datetime.now() - timedelta(seconds=self.window_size)
        while requests_list and requests_list[0] < cutoff_time:
            requests_list.pop(0)
    
    def check_rate_limit(self, endpoint_type):
        requests_list = (self.post_tweet_requests if endpoint_type == 'post_tweet' 
                        else self.search_requests)
        
        self._clean_old_requests(requests_list)
        
        limit_config = self.limits[endpoint_type]
        buffer_limit = limit_config['buffer_limit']
        min_interval = limit_config['min_interval']
        
        # Enforce minimum interval
        if requests_list:
            time_since_last = (datetime.now() - requests_list[-1]).total_seconds()
            if time_since_last < min_interval:
                sleep_time = min_interval - time_since_last
                logging.info(f"Enforcing minimum interval for {endpoint_type}. "
                           f"Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        # Check buffer limit
        if len(requests_list) >= buffer_limit:
            sleep_time = (requests_list[0] - 
                         (datetime.now() - timedelta(seconds=self.window_size))).total_seconds()
            if sleep_time > 0:
                logging.warning(f"Rate limit buffer reached for {endpoint_type}. "
                              f"Sleeping for {sleep_time:.2f} seconds. "
                              f"Current usage: {len(requests_list)}/{buffer_limit}")
                time.sleep(sleep_time)
                self._clean_old_requests(requests_list)
        
        # Log high usage
        current_usage = len(requests_list)
        if current_usage > buffer_limit * 0.8:
            logging.warning(f"High rate limit usage for {endpoint_type}: "
                          f"{current_usage}/{buffer_limit} "
                          f"({(current_usage/buffer_limit)*100:.1f}%)")
        
        requests_list.append(datetime.now())

    def get_current_usage(self, endpoint_type):
        requests_list = (self.post_tweet_requests if endpoint_type == 'post_tweet' 
                        else self.search_requests)
        self._clean_old_requests(requests_list)
        
        limit_config = self.limits[endpoint_type]
        return {
            'current_requests': len(requests_list),
            'buffer_limit': limit_config['buffer_limit'],
            'actual_limit': limit_config['actual_limit'],
            'usage_percentage': (len(requests_list) / limit_config['buffer_limit']) * 100
        }

rate_limiter = TwitterRateLimiter()

def rate_limit(endpoint_type):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            rate_limiter.check_rate_limit(endpoint_type)
            
            # Log usage every 10 requests
            usage = rate_limiter.get_current_usage(endpoint_type)
            if usage['current_requests'] % 10 == 0:
                logging.info(
                    f"Rate limit status for {endpoint_type}: "
                    f"{usage['current_requests']}/{usage['buffer_limit']} "
                    f"({usage['usage_percentage']:.1f}%)"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


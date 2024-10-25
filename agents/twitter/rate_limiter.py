import logging
import time
from datetime import datetime, timedelta
from functools import wraps


class TwitterRateLimiter:
    def __init__(self):
        self.post_tweet_requests = []  # 300 per 3 hours -> buffer to 270
        self.search_requests = []      # 180 per 15 min -> buffer to 160
        self.user_lookup_requests = [] # 900 per 15 min -> buffer to 800
        
        self.window_size = {
            'post_tweet': 3 * 60 * 60,  # 3 hours
            'search': 15 * 60,          # 15 minutes
            'user_lookup': 15 * 60      # 15 minutes
        }
        
        self.limits = {
            'post_tweet': {
                'actual_limit': 300,
                'buffer_limit': 270,  # Using 90% of actual limit
                'min_interval': (3 * 60 * 60) / 270  # Minimum time between requests
            },
            'search': {
                'actual_limit': 180,
                'buffer_limit': 160,  # Using ~89% of actual limit
                'min_interval': (15 * 60) / 160  # Minimum time between requests
            },
            'user_lookup': {
                'actual_limit': 900,
                'buffer_limit': 800,  # Using ~89% of actual limit
                'min_interval': (15 * 60) / 800  # Minimum time between requests
            }
        }
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def _clean_old_requests(self, requests_list, endpoint_type):
        cutoff_time = datetime.now() - timedelta(seconds=self.window_size[endpoint_type])
        while requests_list and requests_list[0] < cutoff_time:
            requests_list.pop(0)
    
    def check_rate_limit(self, endpoint_type):
        if endpoint_type == 'post_tweet':
            requests_list = self.post_tweet_requests
        elif endpoint_type == 'search':
            requests_list = self.search_requests
        else:
            requests_list = self.user_lookup_requests
        
        self._clean_old_requests(requests_list, endpoint_type)
        
        limit_config = self.limits[endpoint_type]
        buffer_limit = limit_config['buffer_limit']
        min_interval = limit_config['min_interval']
        
        # For hourly runs, calculate max requests per hour to stay within limits
        hourly_limit = (buffer_limit * 3600) / self.window_size[endpoint_type]
        if len(requests_list) >= hourly_limit:
            sleep_time = 3600 - (datetime.now() - requests_list[-int(hourly_limit)]).total_seconds()
            if sleep_time > 0:
                logging.warning(f"Hourly rate limit approached for {endpoint_type}. "
                              f"Sleeping for {sleep_time:.2f} seconds. "
                              f"Current usage: {len(requests_list)}/{hourly_limit} per hour")
                time.sleep(sleep_time)
                self._clean_old_requests(requests_list, endpoint_type)
        
        # Enforce minimum interval
        if requests_list:
            time_since_last = (datetime.now() - requests_list[-1]).total_seconds()
            if time_since_last < min_interval:
                sleep_time = min_interval - time_since_last
                logging.info(f"Enforcing minimum interval for {endpoint_type}. "
                           f"Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
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
        hourly_limit = (limit_config['buffer_limit'] * 3600) / self.window_size[endpoint_type]
        
        return {
            'current_requests': len(requests_list),
            'buffer_limit': limit_config['buffer_limit'],
            'actual_limit': limit_config['actual_limit'],
            'hourly_limit': hourly_limit,
            'usage_percentage': (len(requests_list) / hourly_limit) * 100
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
                    f"{usage['current_requests']}/{usage['hourly_limit']} per hour "
                    f"({usage['usage_percentage']:.1f}%)"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
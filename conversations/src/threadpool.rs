use tokio::sync::Semaphore;
use std::sync::Arc;
use crate::error::ServiceError;

pub struct ThreadPool {
    semaphore: Arc<Semaphore>,
}

impl ThreadPool {
    pub fn new(size: usize) -> Self {
        Self {
            semaphore: Arc::new(Semaphore::new(size)),
        }
    }

    pub async fn spawn<F, Fut, T>(&self, f: F) -> Result<T, ServiceError>
    where
        F: FnOnce() -> Fut + Send + 'static,
        Fut: std::future::Future<Output = T> + Send + 'static,
        T: Send + 'static,
    {
        // Implementation...
        todo!()
    }
}
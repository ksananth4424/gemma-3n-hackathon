"""
Performance monitoring and metrics collection system
"""

import time
import psutil
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
import logging
from contextlib import contextmanager

from src.models.response_models import ProcessingMetrics


@dataclass
class SystemMetrics:
    """System-level performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used_mb': self.memory_used_mb,
            'memory_available_mb': self.memory_available_mb,
            'disk_usage_percent': self.disk_usage_percent,
            'disk_free_gb': self.disk_free_gb
        }


@dataclass
class PerformanceAlert:
    """Performance alert when thresholds are exceeded"""
    timestamp: datetime
    alert_type: str
    message: str
    value: float
    threshold: float
    severity: str  # 'warning', 'critical'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'alert_type': self.alert_type,
            'message': self.message,
            'value': self.value,
            'threshold': self.threshold,
            'severity': self.severity
        }


class PerformanceMonitor:
    """Real-time performance monitoring system"""
    
    def __init__(
        self,
        collection_interval: float = 5.0,
        max_history_size: int = 1000,
        logger: Optional[logging.Logger] = None
    ):
        self.collection_interval = collection_interval
        self.max_history_size = max_history_size
        self.logger = logger or logging.getLogger(__name__)
        
        # Data storage
        self.system_metrics: deque = deque(maxlen=max_history_size)
        self.processing_metrics: List[ProcessingMetrics] = []
        self.alerts: deque = deque(maxlen=100)
        
        # Monitoring state
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Alert thresholds
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage_percent': 90.0,
            'processing_time_seconds': 300.0
        }
        
        # Callback functions
        self.alert_callbacks: List[Callable[[PerformanceAlert], None]] = []
    
    def start_monitoring(self):
        """Start background monitoring"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        self.logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                metrics = self._collect_system_metrics()
                
                with self._lock:
                    self.system_metrics.append(metrics)
                
                # Check for alerts
                self._check_alerts(metrics)
                
                time.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.collection_interval)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            memory_available_mb=memory.available / (1024 * 1024),
            disk_usage_percent=disk.used / disk.total * 100,
            disk_free_gb=disk.free / (1024 * 1024 * 1024)
        )
    
    def _check_alerts(self, metrics: SystemMetrics):
        """Check if any thresholds are exceeded"""
        checks = [
            ('cpu_percent', metrics.cpu_percent, 'CPU usage'),
            ('memory_percent', metrics.memory_percent, 'Memory usage'),
            ('disk_usage_percent', metrics.disk_usage_percent, 'Disk usage')
        ]
        
        for threshold_key, value, description in checks:
            threshold = self.thresholds.get(threshold_key, 100.0)
            
            if value > threshold:
                severity = 'critical' if value > threshold * 1.1 else 'warning'
                alert = PerformanceAlert(
                    timestamp=datetime.now(),
                    alert_type=threshold_key,
                    message=f"{description} exceeded threshold: {value:.1f}% > {threshold:.1f}%",
                    value=value,
                    threshold=threshold,
                    severity=severity
                )
                
                self._add_alert(alert)
    
    def _add_alert(self, alert: PerformanceAlert):
        """Add alert and notify callbacks"""
        with self._lock:
            self.alerts.append(alert)
        
        # Log the alert
        if alert.severity == 'critical':
            self.logger.critical(alert.message)
        else:
            self.logger.warning(alert.message)
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")
    
    def add_processing_metrics(self, metrics: ProcessingMetrics):
        """Add processing metrics"""
        with self._lock:
            self.processing_metrics.append(metrics)
            
            # Keep only recent metrics
            if len(self.processing_metrics) > self.max_history_size:
                self.processing_metrics = self.processing_metrics[-self.max_history_size:]
        
        # Check processing time threshold
        if metrics.duration_seconds and metrics.duration_seconds > self.thresholds.get('processing_time_seconds', 300):
            alert = PerformanceAlert(
                timestamp=datetime.now(),
                alert_type='processing_time',
                message=f"Processing time exceeded threshold: {metrics.duration_seconds:.1f}s",
                value=metrics.duration_seconds,
                threshold=self.thresholds['processing_time_seconds'],
                severity='warning'
            )
            self._add_alert(alert)
    
    def get_current_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        current_metrics = self._collect_system_metrics()
        
        with self._lock:
            recent_alerts = list(self.alerts)[-10:]  # Last 10 alerts
        
        return {
            'current_metrics': current_metrics.to_dict(),
            'recent_alerts': [alert.to_dict() for alert in recent_alerts],
            'monitoring_active': self._monitoring,
            'thresholds': self.thresholds
        }
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the specified period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            # Filter metrics by time
            recent_system_metrics = [
                m for m in self.system_metrics
                if m.timestamp > cutoff_time
            ]
            
            recent_processing_metrics = [
                m for m in self.processing_metrics
                if m.start_time > cutoff_time
            ]
            
            recent_alerts = [
                a for a in self.alerts
                if a.timestamp > cutoff_time
            ]
        
        # Calculate averages
        avg_cpu = sum(m.cpu_percent for m in recent_system_metrics) / len(recent_system_metrics) if recent_system_metrics else 0
        avg_memory = sum(m.memory_percent for m in recent_system_metrics) / len(recent_system_metrics) if recent_system_metrics else 0
        
        # Processing statistics
        completed_jobs = len(recent_processing_metrics)
        avg_processing_time = sum(
            m.duration_seconds for m in recent_processing_metrics
            if m.duration_seconds
        ) / completed_jobs if completed_jobs > 0 else 0
        
        return {
            'period_hours': hours,
            'system_averages': {
                'cpu_percent': avg_cpu,
                'memory_percent': avg_memory
            },
            'processing_stats': {
                'completed_jobs': completed_jobs,
                'average_processing_time_seconds': avg_processing_time,
                'total_tokens_processed': sum(m.tokens_processed for m in recent_processing_metrics)
            },
            'alerts': {
                'total_count': len(recent_alerts),
                'warning_count': len([a for a in recent_alerts if a.severity == 'warning']),
                'critical_count': len([a for a in recent_alerts if a.severity == 'critical'])
            }
        }
    
    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Add callback function for alerts"""
        self.alert_callbacks.append(callback)
    
    def set_threshold(self, metric: str, value: float):
        """Set alert threshold for a metric"""
        self.thresholds[metric] = value
        self.logger.info(f"Threshold updated: {metric} = {value}")


@contextmanager
def track_performance(
    monitor: PerformanceMonitor,
    operation_name: str,
    file_path: Optional[str] = None,
    model_name: Optional[str] = None
):
    """Context manager for tracking operation performance"""
    
    # Create metrics object
    metrics = ProcessingMetrics(start_time=datetime.now())
    
    # Get initial system state
    initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
    
    try:
        yield metrics
        
    finally:
        # Complete metrics
        metrics.complete()
        
        # Get final system state
        final_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
        metrics.peak_memory_mb = max(initial_memory, final_memory)
        
        # Set additional info
        if model_name:
            metrics.model_used = model_name
        
        # Add to monitor
        monitor.add_processing_metrics(metrics)


class HealthChecker:
    """System health checking functionality"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.last_check: Optional[datetime] = None
        self.health_status: Dict[str, Any] = {}
    
    def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        self.last_check = datetime.now()
        
        checks = {
            'system_resources': self._check_system_resources(),
            'dependencies': self._check_dependencies(),
            'ollama_service': self._check_ollama_service(),
            'file_system': self._check_file_system(),
            'configuration': self._check_configuration()
        }
        
        # Overall health
        all_healthy = all(check.get('healthy', False) for check in checks.values())
        
        self.health_status = {
            'timestamp': self.last_check.isoformat(),
            'overall_healthy': all_healthy,
            'checks': checks
        }
        
        return self.health_status
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource availability"""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Requirements: 2GB RAM, 10GB disk space
            memory_ok = memory.available > 2 * 1024 * 1024 * 1024  # 2GB
            disk_ok = disk.free > 10 * 1024 * 1024 * 1024  # 10GB
            
            return {
                'healthy': memory_ok and disk_ok,
                'memory_available_gb': memory.available / (1024**3),
                'disk_free_gb': disk.free / (1024**3),
                'memory_sufficient': memory_ok,
                'disk_sufficient': disk_ok
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check required dependencies"""
        required_deps = ['ollama', 'fitz', 'whisper', 'cv2', 'docx']
        available_deps = {}
        
        for dep in required_deps:
            try:
                __import__(dep)
                available_deps[dep] = True
            except ImportError:
                available_deps[dep] = False
        
        all_available = all(available_deps.values())
        
        return {
            'healthy': all_available,
            'dependencies': available_deps,
            'missing': [dep for dep, available in available_deps.items() if not available]
        }
    
    def _check_ollama_service(self) -> Dict[str, Any]:
        """Check Ollama service connectivity"""
        try:
            import ollama
            
            # Try to connect
            client = ollama.Client()
            models = client.list()
            
            return {
                'healthy': True,
                'connected': True,
                'models_available': len(models.get('models', [])),
                'models': [model['name'] for model in models.get('models', [])]
            }
        except Exception as e:
            return {
                'healthy': False,
                'connected': False,
                'error': str(e)
            }
    
    def _check_file_system(self) -> Dict[str, Any]:
        """Check file system access"""
        try:
            from pathlib import Path
            
            # Check if we can create temp files
            temp_dir = Path('temp')
            temp_dir.mkdir(exist_ok=True)
            
            test_file = temp_dir / 'health_check.txt'
            test_file.write_text('health check')
            test_file.unlink()
            
            return {
                'healthy': True,
                'can_write': True,
                'temp_directory_accessible': True
            }
        except Exception as e:
            return {
                'healthy': False,
                'can_write': False,
                'error': str(e)
            }
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration validity"""
        try:
            from src.utils.config_manager import ConfigManager
            
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            return {
                'healthy': True,
                'configuration_loaded': True,
                'ollama_url': config.ollama.base_url,
                'models_configured': len(config.ollama.models)
            }
        except Exception as e:
            return {
                'healthy': False,
                'configuration_loaded': False,
                'error': str(e)
            }


# Global instances
_global_monitor = PerformanceMonitor()
_global_health_checker = HealthChecker()

def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor"""
    return _global_monitor

def get_health_checker() -> HealthChecker:
    """Get global health checker"""
    return _global_health_checker

def setup_monitoring(
    start_monitoring: bool = True,
    logger: Optional[logging.Logger] = None
) -> PerformanceMonitor:
    """Setup performance monitoring"""
    global _global_monitor, _global_health_checker
    
    _global_monitor = PerformanceMonitor(logger=logger)
    _global_health_checker = HealthChecker(logger=logger)
    
    if start_monitoring:
        _global_monitor.start_monitoring()
    
    return _global_monitor

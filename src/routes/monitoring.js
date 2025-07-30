const express = require('express');
const router = express.Router();
const InfrastructureMonitor = require('../infrastructure-monitoring');
const monitor = new InfrastructureMonitor();

// Add a new resource to monitor
router.post('/resources', async (req, res) => {
  try {
    const { type, endpoint, credentials, name, customerId } = req.body;
    
    const resource = {
      id: `res_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      endpoint,
      credentials,
      name,
      customerId,
      interval: req.body.interval || 60000,
      status: 'online',
      lastChecked: null
    };
    
    const result = await monitor.addResource(resource);
    res.json(result);
  } catch (error) {
    console.error('Failed to add resource:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get all resources for a customer
router.get('/resources', async (req, res) => {
  try {
    const { customerId } = req.query;
    const resources = await monitor.getCustomerResources(customerId);
    res.json(resources);
  } catch (error) {
    console.error('Failed to fetch resources:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get metrics for a specific resource
router.get('/metrics/:resourceId', async (req, res) => {
  try {
    const { resourceId } = req.params;
    const { range = '1h' } = req.query;
    const metrics = await monitor.getResourceMetrics(resourceId, range);
    res.json(metrics);
  } catch (error) {
    console.error('Failed to fetch metrics:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get aggregated metrics for dashboard
router.get('/aggregated', async (req, res) => {
  try {
    const { customerId, range = '1h' } = req.query;
    const metrics = await monitor.getAggregatedMetrics(customerId, range);
    res.json(metrics);
  } catch (error) {
    console.error('Failed to fetch aggregated metrics:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get resource status
router.get('/status/:resourceId', async (req, res) => {
  try {
    const { resourceId } = req.params;
    const status = await monitor.getResourceStatus(resourceId);
    res.json({ status });
  } catch (error) {
    console.error('Failed to fetch resource status:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get active alerts for a resource
router.get('/alerts/:resourceId', async (req, res) => {
  try {
    const { resourceId } = req.params;
    const alerts = await monitor.getActiveAlerts(resourceId);
    res.json(alerts);
  } catch (error) {
    console.error('Failed to fetch alerts:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get global alerts
router.get('/alerts', async (req, res) => {
  try {
    const { limit = 50 } = req.query;
    const alerts = await monitor.getGlobalAlerts(parseInt(limit));
    res.json(alerts);
  } catch (error) {
    console.error('Failed to fetch global alerts:', error);
    res.status(500).json({ error: error.message });
  }
});

// Add alert rule
router.post('/alerts/:resourceId', async (req, res) => {
  try {
    const { resourceId } = req.params;
    const { metric, condition, threshold, severity } = req.body;
    
    const rule = {
      id: `rule_${Date.now()}`,
      metric,
      condition,
      threshold,
      severity,
      enabled: true
    };
    
    const result = await monitor.addAlertRule(resourceId, rule);
    res.json(result);
  } catch (error) {
    console.error('Failed to add alert rule:', error);
    res.status(500).json({ error: error.message });
  }
});

// Add notification channel
router.post('/notifications/:resourceId', async (req, res) => {
  try {
    const { resourceId } = req.params;
    const { type, ...config } = req.body;
    
    const channel = {
      id: `channel_${Date.now()}`,
      type,
      ...config,
      enabled: true
    };
    
    const result = await monitor.addNotificationChannel(resourceId, channel);
    res.json(result);
  } catch (error) {
    console.error('Failed to add notification channel:', error);
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;

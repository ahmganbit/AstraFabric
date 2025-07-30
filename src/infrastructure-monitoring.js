const redis = require('./redis-connection');
const axios = require('axios');

class InfrastructureMonitor {
  constructor() {
    this.monitoredResources = new Map();
    this.alertRules = new Map();
    this.metricsHistory = new Map();
    this.alertManager = new AlertManager();
  }

  // Add a resource to monitor
  async addResource(resource) {
    const { id, type, endpoint, credentials, customerId } = resource;
    
    // Validate resource
    if (!this.validateResource(resource)) {
      throw new Error('Invalid resource configuration');
    }

    // Store resource in Redis
    await redis.set(`resource:${id}`, JSON.stringify(resource));
    this.monitoredResources.set(id, resource);

    // Store resource in customer's resource list
    await redis.lpush(`customer:${customerId}:resources`, id);
    
    // Start monitoring
    this.startMonitoring(id);

    return { success: true, resourceId: id };
  }

  // Validate resource configuration
  validateResource(resource) {
    const { type, endpoint, credentials } = resource;
    
    switch (type) {
      case 'server':
        return endpoint && credentials?.sshKey;
      case 'database':
        return endpoint && credentials?.username && credentials?.password;
      case 'website':
        return endpoint && /^https?:\/\//.test(endpoint);
      case 'api':
        return endpoint && credentials?.apiKey;
      default:
        return false;
    }
  }

  // Start monitoring a resource
  startMonitoring(resourceId) {
    const resource = this.monitoredResources.get(resourceId);
    
    // Set up monitoring interval
    setInterval(async () => {
      try {
        const metrics = await this.collectMetrics(resource);
        await this.processMetrics(resourceId, metrics);
      } catch (error) {
        console.error(`Monitoring failed for ${resourceId}:`, error);
        await this.handleMonitoringError(resourceId, error);
      }
    }, resource.interval || 60000); // Default 1 minute
  }

  // Collect metrics from resource
  async collectMetrics(resource) {
    const { type, endpoint, credentials } = resource;
    
    switch (type) {
      case 'server':
        return await this.collectServerMetrics(endpoint, credentials);
      case 'database':
        return await this.collectDatabaseMetrics(endpoint, credentials);
      case 'website':
        return await this.collectWebsiteMetrics(endpoint);
      case 'api':
        return await this.collectApiMetrics(endpoint, credentials);
      default:
        throw new Error(`Unknown resource type: ${type}`);
    }
  }

  // Collect server metrics (simplified example)
  async collectServerMetrics(endpoint, credentials) {
    // Implementation would use SSH to connect and collect metrics
    // For now, return mock data
    return {
      cpu: { load1: Math.random() * 2, load5: Math.random() * 2, load15: Math.random() * 2 },
      memory: { total: 8192, used: Math.random() * 8192, free: Math.random() * 8192, percent: Math.random() * 100 },
      disk: { total: 100, used: Math.random() * 100, free: Math.random() * 100, percent: Math.random() * 100 },
      timestamp: Date.now()
    };
  }

  // Collect database metrics (simplified example)
  async collectDatabaseMetrics(endpoint, credentials) {
    // Implementation would connect to database and collect metrics
    // For now, return mock data
    return {
      connections: Math.floor(Math.random() * 100),
      threads: Math.floor(Math.random() * 20),
      queries: Math.floor(Math.random() * 10000),
      slowQueries: Math.floor(Math.random() * 10),
      uptime: Math.floor(Math.random() * 86400),
      timestamp: Date.now()
    };
  }

  // Collect website metrics
  async collectWebsiteMetrics(endpoint) {
    try {
      const start = Date.now();
      const response = await axios.get(endpoint, {
        timeout: 10000,
        validateStatus: () => true
      });
      const responseTime = Date.now() - start;
      
      return {
        responseTime,
        statusCode: response.status,
        size: response.headers['content-length'] || 0,
        timestamp: Date.now()
      };
    } catch (error) {
      throw new Error(`Website monitoring failed: ${error.message}`);
    }
  }

  // Collect API metrics
  async collectApiMetrics(endpoint, credentials) {
    try {
      const start = Date.now();
      const response = await axios.get(endpoint, {
        headers: {
          'Authorization': `Bearer ${credentials.apiKey}`
        },
        timeout: 10000,
        validateStatus: () => true
      });
      const responseTime = Date.now() - start;
      
      return {
        responseTime,
        statusCode: response.status,
        size: response.headers['content-length'] || 0,
        timestamp: Date.now()
      };
    } catch (error) {
      throw new Error(`API monitoring failed: ${error.message}`);
    }
  }

  // Process collected metrics
  async processMetrics(resourceId, metrics) {
    // Store metrics in Redis
    await this.storeMetrics(resourceId, metrics);
    
    // Check alert rules
    await this.checkAlertRules(resourceId, metrics);
    
    // Update dashboard
    this.updateDashboard(resourceId, metrics);
  }

  // Store metrics in Redis
  async storeMetrics(resourceId, metrics) {
    try {
      // Get existing metrics
      let history = await redis.get(`metrics:${resourceId}`);
      history = history ? JSON.parse(history) : [];
      
      // Add new metrics
      history.push(metrics);
      
      // Keep only last 1000 entries
      if (history.length > 1000) {
        history = history.slice(-1000);
      }
      
      // Store back in Redis with expiration
      await redis.set(`metrics:${resourceId}`, JSON.stringify(history), 7 * 24 * 60 * 60); // 7 days
      
      // Also store latest metrics in a hash for quick access
      await redis.hset(`latest:${resourceId}`, 'data', JSON.stringify(metrics));
      await redis.expire(`latest:${resourceId}`, 24 * 60 * 60); // 24 hours
      
    } catch (error) {
      console.error('Failed to store metrics:', error);
    }
  }

  // Handle monitoring errors
  async handleMonitoringError(resourceId, error) {
    console.error(`Monitoring error for ${resourceId}:`, error);
    
    // Trigger error alert
    await this.alertManager.triggerAlert({
      resourceId,
      metric: 'monitoring',
      value: 'error',
      threshold: 'none',
      condition: 'error',
      severity: 'critical',
      timestamp: Date.now(),
      message: error.message
    });
  }

  // Update dashboard with new metrics
  updateDashboard(resourceId, metrics) {
    // Emit to WebSocket clients
    if (this.io) {
      this.io.emit('metrics-update', {
        resourceId,
        metrics
      });
    }
  }

  // Add alert rule
  async addAlertRule(resourceId, rule) {
    try {
      const rules = await this.getAlertRules(resourceId);
      rules.push(rule);
      
      // Store rules in Redis
      await redis.set(`alerts:${resourceId}`, JSON.stringify(rules));
      this.alertRules.set(resourceId, rules);
      
      return { success: true };
    } catch (error) {
      console.error('Failed to add alert rule:', error);
      throw error;
    }
  }

  // Get alert rules
  async getAlertRules(resourceId) {
    try {
      const rulesData = await redis.get(`alerts:${resourceId}`);
      return rulesData ? JSON.parse(rulesData) : [];
    } catch (error) {
      console.error('Failed to get alert rules:', error);
      return [];
    }
  }

  // Get notification channels
  async getNotificationChannels(resourceId) {
    try {
      const channelsData = await redis.get(`notifications:${resourceId}`);
      return channelsData ? JSON.parse(channelsData) : [];
    } catch (error) {
      console.error('Failed to get notification channels:', error);
      return [];
    }
  }

  // Add notification channel
  async addNotificationChannel(resourceId, channel) {
    try {
      const channels = await this.getNotificationChannels(resourceId);
      channels.push(channel);
      
      // Store channels in Redis
      await redis.set(`notifications:${resourceId}`, JSON.stringify(channels));
      
      return { success: true };
    } catch (error) {
      console.error('Failed to add notification channel:', error);
      throw error;
    }
  }

  // Get resource status
  async getResourceStatus(resourceId) {
    try {
      const latestData = await redis.hget(`latest:${resourceId}`, 'data');
      if (!latestData) return 'unknown';
      
      const metrics = JSON.parse(latestData);
      const now = Date.now();
      
      // If last check was more than 5 minutes ago, consider it offline
      if (now - metrics.timestamp > 5 * 60 * 1000) {
        return 'offline';
      }
      
      // Check for critical alerts
      const alerts = await this.getActiveAlerts(resourceId);
      const criticalAlerts = alerts.filter(alert => alert.severity === 'critical');
      
      if (criticalAlerts.length > 0) {
        return 'critical';
      }
      
      // Check for warning alerts
      const warningAlerts = alerts.filter(alert => alert.severity === 'warning');
      if (warningAlerts.length > 0) {
        return 'warning';
      }
      
      return 'online';
    } catch (error) {
      console.error('Failed to get resource status:', error);
      return 'unknown';
    }
  }

  // Get active alerts
  async getActiveAlerts(resourceId) {
    try {
      const alertsData = await redis.get(`activeAlerts:${resourceId}`);
      return alertsData ? JSON.parse(alertsData) : [];
    } catch (error) {
      console.error('Failed to get active alerts:', error);
      return [];
    }
  }

  // Store active alert
  async storeActiveAlert(resourceId, alert) {
    try {
      let alerts = await this.getActiveAlerts(resourceId);
      
      // Check if similar alert already exists
      const existingAlertIndex = alerts.findIndex(a => 
        a.metric === alert.metric && a.condition === alert.condition
      );
      
      if (existingAlertIndex >= 0) {
        // Update existing alert
        alerts[existingAlertIndex] = alert;
      } else {
        // Add new alert
        alerts.push(alert);
      }
      
      // Store alerts in Redis
      await redis.set(`activeAlerts:${resourceId}`, JSON.stringify(alerts), 24 * 60 * 60); // 24 hours
      
      // Also store in global alerts list
      await redis.lpush('globalAlerts', JSON.stringify(alert));
      await redis.expire('globalAlerts', 7 * 24 * 60 * 60); // 7 days
      
    } catch (error) {
      console.error('Failed to store active alert:', error);
    }
  }

  // Clear active alert
  async clearActiveAlert(resourceId, metric) {
    try {
      let alerts = await this.getActiveAlerts(resourceId);
      alerts = alerts.filter(a => a.metric !== metric);
      
      // Store updated alerts
      await redis.set(`activeAlerts:${resourceId}`, JSON.stringify(alerts));
      
    } catch (error) {
      console.error('Failed to clear active alert:', error);
    }
  }

  // Check alert rules
  async checkAlertRules(resourceId, metrics) {
    const rules = await this.getAlertRules(resourceId);
    
    for (const rule of rules) {
      if (!rule.enabled) continue;
      
      const { metric, condition, threshold, severity } = rule;
      
      let value;
      switch (metric) {
        case 'cpu':
          value = metrics.cpu?.load1 || 0;
          break;
        case 'memory':
          value = metrics.memory?.percent || 0;
          break;
        case 'disk':
          value = metrics.disk?.percent || 0;
          break;
        case 'responseTime':
          value = metrics.responseTime || 0;
          break;
        case 'statusCode':
          value = metrics.statusCode || 200;
          break;
        default:
          continue;
      }
      
      let triggered = false;
      switch (condition) {
        case 'greater_than':
          triggered = value > threshold;
          break;
        case 'less_than':
          triggered = value < threshold;
          break;
        case 'equals':
          triggered = value === threshold;
          break;
      }
      
      if (triggered) {
        const alert = {
          resourceId,
          metric,
          value,
          threshold,
          condition,
          severity,
          timestamp: Date.now()
        };
        
        // Store active alert
        await this.storeActiveAlert(resourceId, alert);
        
        // Trigger notification
        const channels = await this.getNotificationChannels(resourceId);
        for (const channel of channels) {
          await this.alertManager.sendNotification(channel, alert);
        }
      } else {
        // Clear alert if condition is no longer met
        await this.clearActiveAlert(resourceId, metric);
      }
    }
  }

  // Get all resources for a customer
  async getCustomerResources(customerId) {
    try {
      // Get resource IDs for customer
      const resourceIds = await redis.lrange(`customer:${customerId}:resources`, 0, -1);
      
      const resources = [];
      for (const id of resourceIds) {
        const resourceData = await redis.get(`resource:${id}`);
        if (resourceData) {
          const resource = JSON.parse(resourceData);
          resources.push({
            id,
            ...resource,
            metrics: await this.getResourceMetrics(id)
          });
        }
      }
      
      return resources;
    } catch (error) {
      console.error('Failed to get customer resources:', error);
      return [];
    }
  }

  // Get resource metrics from Redis
  async getResourceMetrics(resourceId, timeRange = '1h') {
    try {
      const history = await redis.get(`metrics:${resourceId}`);
      if (!history) return [];
      
      const metrics = JSON.parse(history);
      const now = Date.now();
      let rangeMs;
      
      switch (timeRange) {
        case '1h':
          rangeMs = 60 * 60 * 1000;
          break;
        case '24h':
          rangeMs = 24 * 60 * 60 * 1000;
          break;
        case '7d':
          rangeMs = 7 * 24 * 60 * 60 * 1000;
          break;
        default:
          rangeMs = 60 * 60 * 1000;
      }
      
      return metrics.filter(m => now - m.timestamp <= rangeMs);
    } catch (error) {
      console.error('Failed to get resource metrics:', error);
      return [];
    }
  }

  // Get aggregated metrics for dashboard
  async getAggregatedMetrics(customerId, timeRange = '1h') {
    try {
      const resources = await this.getCustomerResources(customerId);
      const aggregatedMetrics = {
        totalResources: resources.length,
        onlineResources: 0,
        offlineResources: 0,
        warningResources: 0,
        criticalResources: 0,
        cpuAverage: 0,
        memoryAverage: 0,
        diskAverage: 0,
        responseTimeAverage: 0,
        alerts: []
      };
      
      let cpuSum = 0;
      let memorySum = 0;
      let diskSum = 0;
      let responseTimeSum = 0;
      let metricsCount = 0;
      
      for (const resource of resources) {
        const status = await this.getResourceStatus(resource.id);
        
        switch (status) {
          case 'online':
            aggregatedMetrics.onlineResources++;
            break;
          case 'offline':
            aggregatedMetrics.offlineResources++;
            break;
          case 'warning':
            aggregatedMetrics.warningResources++;
            break;
          case 'critical':
            aggregatedMetrics.criticalResources++;
            break;
        }
        
        // Get latest metrics
        const latestData = await redis.hget(`latest:${resource.id}`, 'data');
        if (latestData) {
          const metrics = JSON.parse(latestData);
          
          if (metrics.cpu) {
            cpuSum += metrics.cpu.load1;
            metricsCount++;
          }
          
          if (metrics.memory) {
            memorySum += metrics.memory.percent;
          }
          
          if (metrics.disk) {
            diskSum += metrics.disk.percent;
          }
          
          if (metrics.responseTime) {
            responseTimeSum += metrics.responseTime;
          }
        }
        
        // Get active alerts
        const alerts = await this.getActiveAlerts(resource.id);
        aggregatedMetrics.alerts.push(...alerts);
      }
      
      // Calculate averages
      if (metricsCount > 0) {
        aggregatedMetrics.cpuAverage = cpuSum / metricsCount;
      }
      
      if (resources.length > 0) {
        aggregatedMetrics.memoryAverage = memorySum / resources.length;
        aggregatedMetrics.diskAverage = diskSum / resources.length;
        aggregatedMetrics.responseTimeAverage = responseTimeSum / resources.length;
      }
      
      return aggregatedMetrics;
    } catch (error) {
      console.error('Failed to get aggregated metrics:', error);
      return null;
    }
  }

  // Get global alerts
  async getGlobalAlerts(limit = 50) {
    try {
      const alertsData = await redis.lrange('globalAlerts', 0, limit - 1);
      return alertsData.map(alert => JSON.parse(alert));
    } catch (error) {
      console.error('Failed to get global alerts:', error);
      return [];
    }
  }
}

// Alert Manager
class AlertManager {
  constructor() {
    this.alertHistory = [];
  }

  // Trigger an alert
  async triggerAlert(alert) {
    // Store alert
    this.alertHistory.push(alert);
    
    // Log alert
    console.log('Alert triggered:', alert);
  }

  // Send notification
  async sendNotification(channel, alert) {
    switch (channel.type) {
      case 'email':
        await this.sendEmailNotification(channel, alert);
        break;
      case 'sms':
        await this.sendSmsNotification(channel, alert);
        break;
      case 'webhook':
        await this.sendWebhookNotification(channel, alert);
        break;
      case 'slack':
        await this.sendSlackNotification(channel, alert);
        break;
    }
  }

  // Send email notification
  async sendEmailNotification(channel, alert) {
    const nodemailer = require('nodemailer');
    const transporter = nodemailer.createTransport({
      service: 'gmail',
      auth: {
        user: process.env.ALERT_EMAIL,
        pass: process.env.ALERT_EMAIL_PASSWORD
      }
    });
    
    const mailOptions = {
      from: process.env.ALERT_EMAIL,
      to: channel.address,
      subject: `AstraFabric Alert: ${alert.metric} ${alert.condition} ${alert.threshold}`,
      html: `
        <h2>Infrastructure Alert</h2>
        <p><strong>Resource:</strong> ${alert.resourceId}</p>
        <p><strong>Metric:</strong> ${alert.metric}</p>
        <p><strong>Value:</strong> ${alert.value}</p>
        <p><strong>Threshold:</strong> ${alert.threshold}</p>
        <p><strong>Condition:</strong> ${alert.condition}</p>
        <p><strong>Severity:</strong> ${alert.severity}</p>
        <p><strong>Time:</strong> ${new Date(alert.timestamp).toLocaleString()}</p>
        ${alert.message ? `<p><strong>Message:</strong> ${alert.message}</p>` : ''}
      `
    };
    
    await transporter.sendMail(mailOptions);
  }

  // Send SMS notification
  async sendSmsNotification(channel, alert) {
    const twilio = require('twilio');
    const client = twilio(process.env.TWILIO_ACCOUNT_SID, process.env.TWILIO_AUTH_TOKEN);
    
    await client.messages.create({
      body: `AstraFabric Alert: ${alert.metric} ${alert.condition} ${alert.threshold} on ${alert.resourceId}`,
      from: process.env.TWILIO_PHONE_NUMBER,
      to: channel.phone
    });
  }

  // Send webhook notification
  async sendWebhookNotification(channel, alert) {
    await axios.post(channel.url, {
      alert,
      timestamp: Date.now(),
      source: 'astrafabric'
    });
  }

  // Send Slack notification
  async sendSlackNotification(channel, alert) {
    const webhook = require('slack-webhook');
    const slack = new webhook.Slack(channel.webhookUrl);
    
    await slack.send({
      text: `AstraFabric Alert: ${alert.metric} ${alert.condition} ${alert.threshold}`,
      attachments: [
        {
          color: alert.severity === 'critical' ? 'danger' : 'warning',
          fields: [
            { title: 'Resource', value: alert.resourceId, short: true },
            { title: 'Metric', value: alert.metric, short: true },
            { title: 'Value', value: alert.value.toString(), short: true },
            { title: 'Threshold', value: alert.threshold.toString(), short: true },
            { title: 'Severity', value: alert.severity, short: true },
            { title: 'Time', value: new Date(alert.timestamp).toLocaleString(), short: false }
          ]
        }
      ]
    });
  }
}

module.exports = InfrastructureMonitor;

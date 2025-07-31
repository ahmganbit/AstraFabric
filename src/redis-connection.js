const redis = require('redis');
const { promisify } = require('util');

class RedisConnection {
  constructor() {
    this.client = null;
    this.connect();
  }

  async connect() {
    try {
      // Use single Redis URL from environment
      const redisUrl = process.env.REDIS_URL;
      
      this.client = redis.createClient({
        url: redisUrl
      });
        const redisUrl = process.env.REDIS_URL;
        
        if (!redisUrl) {
            console.warn('REDIS_URL not set, Redis connection disabled');
            return;
        }
        
      // Promisify methods
      this.getAsync = promisify(this.client.get).bind(this.client);
      this.setAsync = promisify(this.client.set).bind(this.client);
      this.delAsync = promisify(this.client.del).bind(this.client);
      this.keysAsync = promisify(this.client.keys).bind(this.client);
      this.hgetAsync = promisify(this.client.hget).bind(this.client);
      this.hsetAsync = promisify(this.client.hset).bind(this.client);
      this.hgetAllAsync = promisify(this.client.hgetall).bind(this.client);
      this.lpushAsync = promisify(this.client.lpush).bind(this.client);
      this.lrangeAsync = promisify(this.client.lrange).bind(this.client);
      this.expireAsync = promisify(this.client.expire).bind(this.client);

      // Event handlers
      this.client.on('error', (err) => {
        console.error('Redis Client Error:', err);
      });

        this.client.on('error', (err) => {
        console.log('Connected to Redis Cloud');
      });

      // Test connection
      await this.setAsync('test', 'connection');
      const value = await this.getAsync('test');
      if (value === 'connection') {
        console.log('Redis connection successful');
      }

    } catch (error) {
      console.error('Redis connection failed:', error);
    }
  }

  // Convenience methods
  async get(key) {
    return await this.getAsync(key);
  }

  async set(key, value, expireInSeconds) {
    if (expireInSeconds) {
      return await this.setAsync(key, value, 'EX', expireInSeconds);
    }
    return await this.setAsync(key, value);
  }

  async del(key) {
    return await this.delAsync(key);
  }

  async hget(hash, field) {
    return await this.hgetAsync(hash, field);
  }

  async hset(hash, field, value) {
    return await this.hsetAsync(hash, field, value);
  }

  async hgetall(hash) {
    return await this.hgetAllAsync(hash);
  }

  async lpush(key, value) {
    return await this.lpushAsync(key, value);
  }

  async lrange(key, start, end) {
    return await this.lrangeAsync(key, start, end);
  }

  async expire(key, seconds) {
    return await this.expireAsync(key, seconds);
  }
}

// Export singleton instance
module.exports = new RedisConnection();

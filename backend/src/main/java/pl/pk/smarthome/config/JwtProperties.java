package pl.pk.smarthome.config;

import java.time.Duration;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "smarthome.jwt")
public record JwtProperties(
		String secret,
		Duration expiration
) {
}

package pl.pk.smarthome.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "smarthome.mqtt")
public record MqttProperties(
		String brokerUrl,
		String clientId,
		String username,
		String password,
		String hubId
) {
}

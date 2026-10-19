package pl.pk.smarthome.mqtt.message;

import java.time.Instant;

// home/<hubId>/climate/telemetry
public record ClimateTelemetryMessage(
		Double temperature,
		Double humidity,
		Instant ts
) {
}

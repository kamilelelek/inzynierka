package pl.pk.smarthome.mqtt.message;

import java.time.Instant;

import pl.pk.smarthome.entity.DeviceState;

// home/<hubId>/<led|heater>/state
public record DeviceStateMessage(
		DeviceState state,
		Instant ts
) {
}

package pl.pk.smarthome.mqtt.message;

import pl.pk.smarthome.entity.DeviceState;

// home/<hubId>/<led|heater>/set
public record DeviceCommandMessage(
		DeviceState state
) {
}

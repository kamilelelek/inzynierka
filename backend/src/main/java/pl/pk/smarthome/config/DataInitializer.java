package pl.pk.smarthome.config;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import pl.pk.smarthome.entity.Device;
import pl.pk.smarthome.entity.DeviceType;
import pl.pk.smarthome.repository.DeviceRepository;

// Tworzy przy starcie brakujące rekordy, których wymaga reszta aplikacji.
@Slf4j
@Component
@RequiredArgsConstructor
public class DataInitializer implements ApplicationRunner {

	private final DeviceRepository deviceRepository;

	@Override
	@Transactional
	public void run(ApplicationArguments args) {
		// Kody muszą odpowiadać segmentom topiców na Pi: home/<hub>/led/..., home/<hub>/heater/...
		ensureDevice("led", "Oświetlenie LED", DeviceType.LIGHT);
		ensureDevice("heater", "Grzałka", DeviceType.HEATER);
	}

	private void ensureDevice(String code, String name, DeviceType type) {
		if (deviceRepository.findByCode(code).isPresent()) {
			return;
		}
		Device device = new Device();
		device.setCode(code);
		device.setName(name);
		device.setType(type);
		deviceRepository.save(device);
		log.info("Dodano urządzenie {} ({})", code, name);
	}

}

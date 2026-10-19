package pl.pk.smarthome.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import pl.pk.smarthome.entity.ThermostatSettings;

public interface ThermostatSettingsRepository extends JpaRepository<ThermostatSettings, Long> {
}

package pl.pk.smarthome.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import pl.pk.smarthome.entity.DeviceStateChange;

public interface DeviceStateChangeRepository extends JpaRepository<DeviceStateChange, Long> {
}

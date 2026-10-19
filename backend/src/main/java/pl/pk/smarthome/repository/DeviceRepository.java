package pl.pk.smarthome.repository;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import pl.pk.smarthome.entity.Device;

public interface DeviceRepository extends JpaRepository<Device, Long> {

	Optional<Device> findByCode(String code);

}

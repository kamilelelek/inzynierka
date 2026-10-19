package pl.pk.smarthome.repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import pl.pk.smarthome.entity.ClimateReading;

public interface ClimateReadingRepository extends JpaRepository<ClimateReading, Long> {

	Optional<ClimateReading> findTopByOrderByMeasuredAtDesc();

	List<ClimateReading> findByMeasuredAtBetweenOrderByMeasuredAtAsc(Instant from, Instant to);

}

package pl.pk.smarthome.repository;

import java.util.List;

import org.springframework.data.domain.Limit;
import org.springframework.data.jpa.repository.JpaRepository;
import pl.pk.smarthome.entity.MotionEvent;

public interface MotionEventRepository extends JpaRepository<MotionEvent, Long> {

	List<MotionEvent> findByOrderByDetectedAtDesc(Limit limit);

}

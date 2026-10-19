package pl.pk.smarthome.entity;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

// Zdarzenie PIR (topic motion/event)
@Entity
@Table(name = "motion_events", indexes = @Index(columnList = "detectedAt"))
@Getter
@Setter
@NoArgsConstructor
public class MotionEvent {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@Column(nullable = false)
	private boolean motion;

	@Column(nullable = false)
	private Instant detectedAt;

}

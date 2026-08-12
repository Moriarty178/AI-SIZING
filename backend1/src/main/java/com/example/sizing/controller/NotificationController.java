package com.example.sizing.controller;

import com.example.sizing.dto.SendNotificationRequest;
import com.example.sizing.model.Notification;
import com.example.sizing.repository.NotificationRepository;
import com.example.sizing.service.NotificationService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/notifications")
@CrossOrigin(origins = "*")
public class NotificationController {
    private static final Logger log = LoggerFactory.getLogger(NotificationController.class);

    private final NotificationService notificationService;
    private final NotificationRepository notificationRepository;

    public NotificationController(NotificationService notificationService,
                                  NotificationRepository notificationRepository) {
        this.notificationService = notificationService;
        this.notificationRepository = notificationRepository;
    }

    /**
     * Manual/test SMS send endpoint.
     * POST /api/notifications/send
     */
    @PostMapping("/send")
    public ResponseEntity<String> send(@RequestBody SendNotificationRequest request) {
        log.info("POST /api/notifications/send - projectId={}, recipient={}, phone={}",
                request.getProjectId(), request.getRecipientUserId(), request.getPhoneNumber());
        notificationService.sendManualNotification(request);
        return ResponseEntity.ok("Notification queued for sending");
    }

    /**
     * List notifications by project.
     * GET /api/notifications/project/{projectId}
     */
    @GetMapping("/project/{projectId}")
    public ResponseEntity<List<Notification>> getByProject(@PathVariable String projectId) {
        return ResponseEntity.ok(notificationRepository.findByProjectIdOrderByCreatedAtDesc(projectId));
    }

    /**
     * List notifications by recipient user.
     * GET /api/notifications/user/{userId}
     */
    @GetMapping("/user/{userId}")
    public ResponseEntity<List<Notification>> getByUser(@PathVariable String userId) {
        return ResponseEntity.ok(notificationRepository.findByRecipientUserIdOrderByCreatedAtDesc(userId));
    }

    /**
     * List all notifications with a given status.
     * GET /api/notifications/status/{status}
     */
    @GetMapping("/status/{status}")
    public ResponseEntity<List<Notification>> getByStatus(@PathVariable String status) {
        try {
            Notification.NotificationStatus s = Notification.NotificationStatus.valueOf(status.toUpperCase());
            return ResponseEntity.ok(notificationRepository.findByStatus(s));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().build();
        }
    }

    /**
     * List all notifications.
     * GET /api/notifications
     */
    @GetMapping
    public ResponseEntity<List<Notification>> getAll() {
        return ResponseEntity.ok(notificationRepository.findAll());
    }
}
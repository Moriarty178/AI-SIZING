package com.example.sizing.service;

import com.example.sizing.dto.SendNotificationRequest;
import com.example.sizing.exception.BadRequestException;
import com.example.sizing.model.Notification;
import com.example.sizing.model.Notification.MessageType;
import com.example.sizing.model.Notification.NotificationStatus;
import com.example.sizing.model.Project;
import com.example.sizing.model.User;
import com.example.sizing.repository.NotificationRepository;
import com.example.sizing.repository.ProjectRepository;
import com.example.sizing.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.text.Normalizer;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.regex.Pattern;

@Service
public class NotificationService {
    private static final Logger log = LoggerFactory.getLogger(NotificationService.class);

    private static final Pattern DIACRITICS = Pattern.compile(
            "[\\p{InCombiningDiacriticalMarks}]");

    private final NotificationRepository notificationRepository;
    private final UserRepository userRepository;
    private final ProjectRepository projectRepository;
    private final SmsDispatcher smsDispatcher;

    public NotificationService(NotificationRepository notificationRepository,
                               UserRepository userRepository,
                               ProjectRepository projectRepository,
                               SmsDispatcher smsDispatcher) {
        this.notificationRepository = notificationRepository;
        this.userRepository = userRepository;
        this.projectRepository = projectRepository;
        this.smsDispatcher = smsDispatcher;
    }

    // =====================
    // Workflow trigger methods
    // =====================

    /**
     * Event 1: User submits project for review (status changes to THAM_DINH).
     * Notifies assigned admin1 + all admin2 users.
     */
    public void onProjectSubmitted(String projectId, String actorUserId) {
        log.info("[NOTIFY] onProjectSubmitted: projectId={}, actorUserId={}", projectId, actorUserId);

        Project project = projectRepository.findById(projectId).orElse(null);
        String projectName = project != null ? project.getName() : projectId;
        log.info("[NOTIFY] onProjectSubmitted: project found={}, name={}, assignedAdmin1Id={}",
                project != null, projectName, project != null ? project.getAssignedAdmin1Id() : null);

        if (project != null && project.getAssignedAdmin1Id() != null) {
            log.info("[NOTIFY] onProjectSubmitted: notifying assignedAdmin1 {}", project.getAssignedAdmin1Id());
            notifyUser(project.getAssignedAdmin1Id(), projectId, actorUserId,
                    MessageType.PROJECT_SUBMITTED, projectName);
        } else {
            log.info("[NOTIFY] onProjectSubmitted: skipping admin1 notify — assignedAdmin1Id is null");
        }

        List<User> admin2Users = userRepository.findByRole("admin2");
        log.info("[NOTIFY] onProjectSubmitted: found {} admin2 users", admin2Users.size());
        for (User admin2 : admin2Users) {
            log.info("[NOTIFY] onProjectSubmitted: notifying admin2 user id={}, username={}, phone={}",
                    admin2.getId(), admin2.getUsername(), admin2.getPhoneNumber());
            notifyUser(admin2.getId(), projectId, actorUserId,
                    MessageType.PROJECT_SUBMITTED, projectName);
        }
    }

    /**
     * Event 2: Admin1 forwards project for approval (status changes to PHE_DUYET).
     * Notifies all admin2 users.
     */
    public void onAdmin1Forwarded(String projectId, String actorUserId) {
        log.info("Notification trigger: project {} forwarded by admin1", projectId);

        Project project = projectRepository.findById(projectId).orElse(null);
        String projectName = project != null ? project.getName() : projectId;

        List<User> admin2Users = userRepository.findByRole("admin2");
        for (User admin2 : admin2Users) {
            notifyUser(admin2.getId(), projectId, actorUserId,
                    MessageType.ADMIN1_FORWARDED, projectName);
        }
    }

    /**
     * Event 3: Admin2 approves project (status becomes HOAN_THANH).
     * Notifies project owner + assigned admin1.
     */
    public void onProjectApproved(String projectId, String actorUserId) {
        log.info("Notification trigger: project {} approved", projectId);

        Project project = projectRepository.findById(projectId).orElse(null);
        String projectName = project != null ? project.getName() : projectId;

        if (project != null && project.getUserId() != null) {
            notifyUser(project.getUserId(), projectId, actorUserId,
                    MessageType.PROJECT_APPROVED, projectName);
        }

        if (project != null && project.getAssignedAdmin1Id() != null) {
            notifyUser(project.getAssignedAdmin1Id(), projectId, actorUserId,
                    MessageType.PROJECT_APPROVED, projectName);
        }
    }

    /**
     * Event 4: Admin1 or Admin2 returns project to sizing.
     * Notifies project owner. If admin2 returns, also notifies assigned admin1.
     */
    public void onProjectReturnedSizing(String projectId, String actorUserId, String actorRole) {
        log.info("Notification trigger: project {} returned to sizing by {} ({})", projectId, actorUserId, actorRole);

        Project project = projectRepository.findById(projectId).orElse(null);
        String projectName = project != null ? project.getName() : projectId;

        if (project != null && project.getUserId() != null) {
            notifyUser(project.getUserId(), projectId, actorUserId,
                    MessageType.PROJECT_RETURNED_SIZING, projectName);
        }

        if ("admin2".equalsIgnoreCase(actorRole) && project != null && project.getAssignedAdmin1Id() != null) {
            notifyUser(project.getAssignedAdmin1Id(), projectId, actorUserId,
                    MessageType.PROJECT_RETURNED_SIZING, projectName);
        }
    }

    /**
     * Event 5: Admin2 assigns admin1 to a project.
     * Notifies the assigned admin1.
     */
    public void onAdmin1Assigned(String projectId, String admin1UserId) {
        log.info("Notification trigger: admin1 {} assigned to project {}", admin1UserId, projectId);

        Project project = projectRepository.findById(projectId).orElse(null);
        String projectName = project != null ? project.getName() : projectId;

        notifyUser(admin1UserId, projectId, null, MessageType.ADMIN1_ASSIGNED, projectName);
    }

    // =====================
    // Core notification dispatch
    // =====================

    /**
     * Core method: creates notification record and fires SMS asynchronously.
     * Skips if recipient has no phone number or if already sent.
     * Note: intentionally NOT @Transactional — called from transactional contexts
     * (update/approve flow) where we must never mark the outer tx as rollback.
     */
    public void notifyUser(String recipientUserId, String projectId, String actorUserId,
                           MessageType messageType, String projectName) {
        log.info("[NOTIFY] notifyUser: recipientId={}, projectId={}, type={}", recipientUserId, projectId, messageType);

        if (recipientUserId == null || recipientUserId.isBlank()) {
            log.warn("[NOTIFY] notifyUser SKIP: recipientUserId is null/blank");
            return;
        }

        Optional<User> recipientOpt = userRepository.findById(recipientUserId);
        if (recipientOpt.isEmpty()) {
            log.warn("[NOTIFY] notifyUser SKIP: recipient user {} not found in DB", recipientUserId);
            return;
        }
        User recipient = recipientOpt.get();

        log.info("[NOTIFY] notifyUser: user found id={}, username={}, phone='{}'",
                recipient.getId(), recipient.getUsername(), recipient.getPhoneNumber());

        if (recipient.getPhoneNumber() == null || recipient.getPhoneNumber().isBlank()) {
            log.warn("[NOTIFY] notifyUser SKIP: user {} has no phone number", recipient.getUsername());
            return;
        }

        String message = buildMessage(messageType, projectName);
        log.info("[NOTIFY] notifyUser: built message='{}'", message);

        Notification notification = new Notification();
        notification.setId(UUID.randomUUID().toString());
        notification.setProjectId(projectId);
        notification.setActorUserId(actorUserId);
        notification.setRecipientUserId(recipientUserId);
        notification.setRecipientPhone(recipient.getPhoneNumber());
        notification.setMessageType(messageType);
        notification.setMessageContent(message);
        notification.setStatus(NotificationStatus.PENDING);
        notification.setRetryCount(0);
        Notification saved = notificationRepository.save(notification);

        log.info("[NOTIFY] notifyUser: SAVED notification record id={}, recipient={}, phone={}, type={}",
                saved.getId(), recipientUserId, recipient.getPhoneNumber(), messageType);

        try {
            smsDispatcher.sendSmsWithRetry(saved.getId(), recipient.getPhoneNumber(), message);
            log.info("[NOTIFY] sendSmsAsync called for notification {} to {}", saved.getId(), recipient.getPhoneNumber());
        } catch (Exception ex) {
            log.error("[NOTIFY] sendSmsAsync threw exception: {}", ex.getMessage(), ex);
        }
    }

    private String removeDiacritics(String input) {
        if (input == null || input.isBlank()) {
            return input;
        }
        String normalized = Normalizer.normalize(input, Normalizer.Form.NFD);
        String withoutDiacritics = DIACRITICS.matcher(normalized).replaceAll("");
        return withoutDiacritics
                .replace('Đ', 'D')
                .replace('đ', 'd');
    }

    // =====================
    // Message templates
    // =====================

    private String buildMessage(MessageType type, String projectName) {
        String cleanProjectName = removeDiacritics(projectName);
        return switch (type) {
            case PROJECT_SUBMITTED -> String.format(
                    "He thong %s da duoc gui tham dinh. Vui long kiem tra va danh gia.", cleanProjectName);
            case ADMIN1_FORWARDED -> String.format(
                    "He thong %s da duoc Admin1 chuyen tien phep duyet. Vui long xem xet va phe duyet.", cleanProjectName);
            case PROJECT_APPROVED -> String.format(
                    "He thong %s da duoc phe duyet hoan thanh.", cleanProjectName);
            case PROJECT_RETURNED_SIZING -> String.format(
                    "He thong %s da bi tra ve Sizing de chinh sua. Vui long kiem tra va cap nhat.", cleanProjectName);
            case ADMIN1_ASSIGNED -> String.format(
                    "Ban duoc chi dinh tham dinh he thong %s. Vui long kiem tra va danh gia.", cleanProjectName);
        };
    }

    // =====================
    // Manual test endpoint handler
    // =====================

    @Transactional
    public void sendManualNotification(SendNotificationRequest request) {
        String phone = request.getPhoneNumber();

        if (phone == null || phone.isBlank()) {
            if (request.getRecipientUserId() != null) {
                User u = userRepository.findById(request.getRecipientUserId()).orElse(null);
                phone = u != null ? u.getPhoneNumber() : null;
            }
        }

        if (phone == null || phone.isBlank()) {
            throw new BadRequestException("No phone number available for notification");
        }

        String rawContent = request.getMessageContent() != null
                ? request.getMessageContent()
                : "Test message from Sizing system";
        String content = removeDiacritics(rawContent);
        String projectId = request.getProjectId() != null ? request.getProjectId() : "MANUAL";
        MessageType msgType = MessageType.PROJECT_SUBMITTED;
        if (request.getMessageType() != null) {
            try {
                msgType = MessageType.valueOf(request.getMessageType());
            } catch (IllegalArgumentException ignored) { }
        }

        Notification notification = new Notification();
        notification.setId(UUID.randomUUID().toString());
        notification.setProjectId(projectId);
        notification.setRecipientUserId(request.getRecipientUserId());
        notification.setRecipientPhone(phone);
        notification.setMessageType(msgType);
        notification.setMessageContent(content);
        notification.setStatus(NotificationStatus.PENDING);
        notification.setRetryCount(0);
        Notification saved = notificationRepository.save(notification);
        log.info("[NOTIFY] sendManualNotification: created notification id={}, phone={}", saved.getId(), phone);

        smsDispatcher.sendSmsWithRetrySync(saved.getId(), phone, content);
    }
}
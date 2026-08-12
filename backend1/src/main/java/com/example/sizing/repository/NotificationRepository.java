package com.example.sizing.repository;

import com.example.sizing.model.Notification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface NotificationRepository extends JpaRepository<Notification, String> {
    List<Notification> findByProjectIdOrderByCreatedAtDesc(String projectId);
    List<Notification> findByRecipientUserIdOrderByCreatedAtDesc(String recipientUserId);
    List<Notification> findByStatus(Notification.NotificationStatus status);
    List<Notification> findByProjectIdAndMessageType(String projectId, Notification.MessageType messageType);
}
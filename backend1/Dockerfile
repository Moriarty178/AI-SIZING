# Backend Spring Boot — build BÊN TRONG Docker (GĐ 6.1, 2026-09-21).
#
# ⚠️ Bản trước chỉ có `COPY target/sizing-*.jar app.jar`: nó chép một jar ĐÃ CÓ
# SẴN. Trên máy chưa từng chạy Maven thì `backend1/target/` trống và
# `docker compose build backend` hỏng ngay — đo 2026-09-21 trên máy nội bộ:
# không có jar nào. Jenkins giấu việc này vì nó chạy Maven ở một stage riêng
# trước khi build image; ai dựng tay thì không có stage ấy.
#
# Hai tầng: tầng `build` biên dịch, tầng chạy chỉ có JRE + jar. Ảnh cuối KHÔNG
# to thêm — Maven và bộ đệm `.m2` nằm lại ở tầng build.

FROM registry.kcntt.net/library/maven:3.9-eclipse-temurin-21-alpine AS build

WORKDIR /build

# Gương Maven nội bộ, ĐÃ CÓ SẴN trong repo (`backend1/.m2/settings.xml`, trỏ
# `nexus-lab.kcntt.net`). Jenkins gắn cùng nội dung ấy từ `/home/sizing`; ở đây
# chép thẳng từ repo để dựng tay cũng chạy được.
#
# ⚠️ Mìn trong file đó: khối `<proxies>` có `<host>...</host>` — đúng chữ ba
# chấm, mà `active=true`. Nó vô hại CHỈ VÌ `nonProxyHosts` có `*.kcntt.net`, nên
# mọi thứ đi thẳng tới Nexus nội bộ. Nếu một ngày Maven phải với ra ngoài
# kcntt.net, đây là chỗ nó sẽ hỏng, và thông báo lỗi sẽ không nhắc tới file này.
COPY .m2/settings.xml /root/.m2/settings.xml

# `pom.xml` TRƯỚC `src`: đổi code mà không đổi phụ thuộc thì Docker dùng lại lớp
# này, khỏi kéo lại ~150 MB. `|| true` vì `go-offline` hay vấp vài plugin mà vẫn
# kéo đủ phần chính — đây chỉ là bước làm ấm bộ đệm; bước dựng thật ở dưới mới
# là bước được phép hỏng.
COPY pom.xml ./
RUN mvn -B -DskipTests dependency:go-offline || true

COPY src ./src
RUN mvn -B -DskipTests clean package

# --------------------------------------------------------------------- chạy --
FROM registry.kcntt.net/library/eclipse-temurin:21-jre-alpine

WORKDIR /app

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# `sizing-*.jar` KHÔNG khớp `sizing-*.jar.original` (jar chưa đóng gói lại của
# Spring Boot) vì glob đòi kết thúc bằng `.jar`.
COPY --from=build --chown=appuser:appgroup /build/target/sizing-*.jar app.jar

EXPOSE 8081

USER appuser

# Ép Java chạy theo múi giờ VN bằng tham số -Duser.timezone
ENTRYPOINT ["java", "-Duser.timezone=Asia/Ho_Chi_Minh", "-XX:+UseG1GC", "-Dfile.encoding=UTF-8", "-jar", "app.jar"]

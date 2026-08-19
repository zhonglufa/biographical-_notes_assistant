#!/bin/sh
# Maven 启动器 —— 绕过本机全局 `mvn` 脚本的缺陷：
# 其用 classworlds 通配符 `plexus-classworlds-*.jar` 拼 classpath，在本 shell 下通配符不展开，
# 导致 java 收到字面量 `*.jar` → ClassNotFoundException: org.codehaus.plexus.classworlds.launcher.Launcher。
# 这里直接用 java 启动 classworlds Launcher，显式指定 boot jar / m2.conf / maven.home，稳定可用。
#
# 用法：先 cd 到 Maven 工程目录（如 server-java），再 `bash ../../scripts/mvn.sh <args>`
export JAVA_HOME="${JAVA_HOME:-/d/JDK2}"
export MAVEN_HOME="${MAVEN_HOME:-E:/简历/.sandbox-tools/apache-maven-3.9.9}"
REPO="${MAVEN_REPO_LOCAL:-E:/mvn-repo}"
exec "$JAVA_HOME/bin/java" \
  -classpath "$MAVEN_HOME/boot/plexus-classworlds-2.8.0.jar" \
  -Dclassworlds.conf="$MAVEN_HOME/bin/m2.conf" \
  -Dmaven.home="$MAVEN_HOME" \
  -Dmaven.repo.local="$REPO" \
  -Dmaven.multiModuleProjectDirectory="$(pwd)" \
  org.codehaus.plexus.classworlds.launcher.Launcher "$@"

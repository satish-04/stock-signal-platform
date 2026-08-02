apiVersion: v1
kind: Namespace
metadata:
  name: {{ .Release.Namespace }}
  labels:
    app: {{ include "stock-signal-app.name" . }}
    environment: {{ .Values.environment | default "development" }}

---
# Common labels
{{- define "stock-signal-app.labels" -}}
helm.sh/chart: {{ include "stock-signal-app.name" . }}-{{ .Chart.Version }}
{{ include "stock-signal-app.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: Helm
{{- end }}

---
# Selector labels
{{- define "stock-signal-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "stock-signal-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

---
# Create unique name
{{- define "stock-signal-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

---
# Full name
{{- define "stock-signal-app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" $name .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}
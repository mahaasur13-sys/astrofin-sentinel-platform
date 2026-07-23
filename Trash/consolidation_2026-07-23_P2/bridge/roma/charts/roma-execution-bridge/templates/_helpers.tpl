{{/*
Expand name of the chart.
*/}}
{{- define "roma-execution-bridge.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "roma-execution-bridge.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "roma-execution-bridge.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "roma-execution-bridge.labels" -}}
helm.sh/chart: {{ include "roma-execution-bridge.chart" . }}
{{ include "roma-execution-bridge.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "roma-execution-bridge.selectorLabels" -}}
app.kubernetes.io/name: {{ include "roma-execution-bridge.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
StorageClass from global or values
*/}}
{{- define "roma-execution-bridge.storageClass" -}}
{{- $sc := .Values.global.storageClass | default "longhorn" }}
{{- if .Values.persistence.checkpoints.storageClass }}
{{- .Values.persistence.checkpoints.storageClass }}
{{- else }}
{{- $sc }}
{{- end }}
{{- end }}

{{/*
Global image pull secrets
*/}}
{{- define "roma-execution-bridge.imagePullSecrets" -}}
{{- with .Values.global.imagePullSecrets }}
imagePullSecrets:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- end }}

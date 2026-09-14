const BASE = "/api";

async function handleResponse(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || "Something went wrong. Please try again.");
  }
  return data;
}

export async function uploadResume(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE}/upload-resume`, {
    method: "POST",
    body: formData,
  });
  return handleResponse(res);
}

export async function analyzeResume(resumeText, targetRole) {
  const res = await fetch(`${BASE}/analyze-resume`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume_text: resumeText, target_role: targetRole || null }),
  });
  return handleResponse(res);
}

export async function fetchSkillGap(resumeText, targetRole) {
  const res = await fetch(`${BASE}/skill-gap`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume_text: resumeText, target_role: targetRole }),
  });
  return handleResponse(res);
}

export async function fetchJobMatch(resumeText, jobDescription) {
  const res = await fetch(`${BASE}/job-match`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume_text: resumeText, job_description: jobDescription }),
  });
  return handleResponse(res);
}

export async function improveBullet(bulletText) {
  const res = await fetch(`${BASE}/improve-bullet`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ bullet_text: bulletText }),
  });
  return handleResponse(res);
}

export async function fetchDemo(targetRole) {
  const params = targetRole ? `?target_role=${encodeURIComponent(targetRole)}` : "";
  const res = await fetch(`${BASE}/demo${params}`);
  return handleResponse(res);
}

export async function fetchJobRoles() {
  const res = await fetch(`${BASE}/job-roles`);
  return handleResponse(res);
}

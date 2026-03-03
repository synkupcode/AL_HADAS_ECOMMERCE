"use client"

import { useState } from "react"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"

export default function ContactPage() {

  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    inquiryType: "",
    message: ""
  })

  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.fullName || !formData.email || !formData.inquiryType || !formData.message) {
      alert("Please fill all fields")
      return
    }

    setLoading(true)
    setSuccess(false)

    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      })

      const data = await response.json()

      if (response.ok) {
        setSuccess(true)
        setFormData({
          fullName: "",
          email: "",
          inquiryType: "",
          message: ""
        })
      } else {
        alert(data.detail || "Failed to send inquiry")
      }

    } catch {
      alert("Server error")
    }

    setLoading(false)
  }

  return (
    <>
      <Navbar />

      <section className="relative min-h-screen flex items-center py-20 md:py-28 bg-gradient-to-br from-[#081a2f] via-[#0d3b66] to-[#081a2f] overflow-hidden">

        <div className="absolute -top-32 -left-32 w-[500px] h-[500px] bg-[#b11217]/20 blur-[140px] rounded-full"></div>
        <div className="absolute -bottom-32 -right-32 w-[600px] h-[600px] bg-[#0a2540]/30 blur-[160px] rounded-full"></div>

        <div className="relative max-w-7xl mx-auto px-6 w-full z-10">

          <div className="grid lg:grid-cols-2 gap-16 xl:gap-24 items-start">

            {/* LEFT */}
            <div className="space-y-10 text-white">

              <div>
                <h1 className="text-4xl md:text-5xl font-bold leading-tight">
                  Let’s Build Something <br />
                  Exceptional Together
                </h1>

                <p className="mt-6 text-white/80 text-lg max-w-lg">
                  Whether you have a product inquiry, bulk order requirement,
                  or need technical assistance — our team is ready to support you.
                </p>
              </div>

              <div className="space-y-8">

                <ContactItem icon={<OfficeIcon />} title="Head Office"
                  content="Kingdom of Saudi Arabia, Riyadh 113513 – Al Takhassusi"
                />

                <ContactItem icon={<MailIcon />} title="Email Address"
                  content="sales@alhadasksa.com"
                />

                <ContactItem icon={<PhoneIcon />} title="Phone Number"
                  content="+966 54 678 4641"
                />

              </div>

              <div className="bg-white/10 border border-white/20 rounded-xl p-5 text-sm text-white/70">
                ⏱ Average response time: Within 24 business hours
              </div>

            </div>

            {/* RIGHT FORM */}
            <div className="text-white">

              <h2 className="text-3xl font-bold mb-4">
                Send an Inquiry
              </h2>

              <p className="text-white/70 mb-8">
                Fill the form below and our team will respond shortly.
              </p>

              <form className="space-y-6" onSubmit={handleSubmit}>

                <InputWithIcon icon={<UserIcon />}>
                  <input type="text" name="fullName"
                    value={formData.fullName}
                    onChange={handleChange}
                    placeholder="Full Name"
                    className="w-full bg-transparent outline-none text-white placeholder-white/50"
                  />
                </InputWithIcon>

                <InputWithIcon icon={<MailIcon />}>
                  <input type="email" name="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="Email Address"
                    className="w-full bg-transparent outline-none text-white placeholder-white/50"
                  />
                </InputWithIcon>

                <InputWithIcon icon={<TagIcon />}>
                  <select name="inquiryType"
                    value={formData.inquiryType}
                    onChange={handleChange}
                    className="w-full bg-transparent outline-none text-white"
                  >
                    <option value="" className="text-black">Select Inquiry Type</option>
                    <option value="Product Inquiry" className="text-black">Product Inquiry</option>
                    <option value="Bulk Order" className="text-black">Bulk Order</option>
                    <option value="Technical/Payment Issue" className="text-black">Technical / Payment Issue</option>
                    <option value="General Business Inquiry" className="text-black">General Business Inquiry</option>
                  </select>
                </InputWithIcon>

                <div className="border border-white/20 rounded-xl p-4 focus-within:border-[#b11217] transition">
                  <textarea rows={5} name="message"
                    value={formData.message}
                    onChange={handleChange}
                    placeholder="Your Message"
                    className="w-full bg-transparent outline-none text-white placeholder-white/50 resize-none"
                  />
                </div>

                <button type="submit"
                  disabled={loading || success}
                  className={`w-full py-3 rounded-xl font-semibold transition-all duration-300 ${
                    success ? "bg-green-600"
                    : "bg-gradient-to-r from-[#b11217] to-[#ff3c3c] hover:scale-[1.02]"
                  }`}
                >
                  {loading ? "Sending..."
                    : success ? "Inquiry Sent Successfully"
                    : "Submit Inquiry"}
                </button>

              </form>

            </div>

          </div>
        </div>
      </section>

      <Footer />
    </>
  )
}

/* COMPONENTS */

function ContactItem({ icon, title, content }: any) {
  return (
    <div className="flex items-start gap-4 group">
      <div className="p-3 rounded-xl bg-white/10 group-hover:bg-[#b11217] transition flex-shrink-0">
        {icon}
      </div>
      <div>
        <p className="font-semibold text-lg">{title}</p>
        <p className="text-white/70 mt-1 text-sm">{content}</p>
      </div>
    </div>
  )
}

function InputWithIcon({ icon, children }: any) {
  return (
    <div className="flex items-center gap-3 border border-white/20 rounded-xl px-4 py-3 focus-within:border-[#b11217] transition">
      {icon}
      {children}
    </div>
  )
}

/* FIXED SVG ICONS */

const baseIcon = "w-5 h-5 flex-shrink-0"

const UserIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
    className={baseIcon}>
    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
)

const MailIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
    className={baseIcon}>
    <rect x="3" y="5" width="18" height="14" rx="2" />
    <path d="M3 7l9 6 9-6" />
  </svg>
)

const PhoneIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
    className={baseIcon}>
    <path d="M22 16.92V21a2 2 0 01-2 2A19.86 19.86 0 013 4a2 2 0 012-2h4l2 5-2 1a16 16 0 006 6l1-2 5 2z" />
  </svg>
)

const OfficeIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
    className={baseIcon}>
    <rect x="3" y="3" width="18" height="18" />
    <path d="M9 21V9h6v12" />
  </svg>
)

const TagIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
    className={baseIcon}>
    <path d="M20 12l-8-8H4v8l8 8 8-8z" />
    <circle cx="7" cy="7" r="1.5" />
  </svg>
)

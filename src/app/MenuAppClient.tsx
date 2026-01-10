'use client'

import { useState } from 'react'
import { uploadMenu, createCompany, deleteCompany, updateBarName, createMessageTemplate, deleteMessageTemplate } from './actions'

// --- Interface Definitions ---
type Bar = {
  id: string;
  name: string;
}

type MessageTemplate = {
  id: string;
  name: string;
  content: string;
}

type Menu = {
  id: string;
  imageUrl: string;
  date: Date;
  createdAt: Date;
  bar: Bar;
}

type Company = {
  id: string;
  name: string;
  contactName: string;
  contactPhone: string;
}

// --- Icons (Inline SVG for cleaner dependency tree) ---
const Icons = {
    Send: () => <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>,
    Upload: () => <svg className="w-8 h-8 text-indigo-500 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>,
    Trash: () => <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>,
    Plus: () => <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>,
    Template: () => <svg className="w-5 h-5 text-gray-400 group-hover:text-indigo-500 transition" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" /></svg>,
    Users: () => <svg className="w-5 h-5 text-indigo-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>,
    Settings: () => <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>,
    Image: () => <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
}

// --- Main Component ---
export default function MenuAppClient({ 
  initialBar, 
  initialTemplates, 
  initialCompanies, 
  initialMenus 
}: { 
  initialBar: Bar | null, 
  initialTemplates: MessageTemplate[], 
  initialCompanies: Company[], 
  initialMenus: Menu[] 
}) {
  const [messageText, setMessageText] = useState(
    initialBar ? `Hola {nombre}, *${initialBar.name}* ha publicado el menú de hoy.` : ''
  )
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans selection:bg-indigo-100 selection:text-indigo-900">
      
      {/* Top Navigation Bar */}
      <nav className="sticky top-0 z-50 backdrop-blur-md bg-white/80 border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
           <div className="flex items-center gap-3">
              <div className="bg-indigo-600 rounded-lg p-1.5 shadow-lg shadow-indigo-500/30">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
              </div>
              <span className="font-bold text-xl tracking-tight text-slate-900">Menu<span className="text-indigo-600">Spreader</span></span>
           </div>
           
           <div className="flex items-center gap-4">
               {/* Quick Bar Name Edit Inline */}
               <form action={updateBarName} className="flex items-center gap-2 bg-slate-100 rounded-full px-3 py-1.5 border border-transparent focus-within:border-indigo-300 focus-within:ring-2 focus-within:ring-indigo-100 transition">
                 <Icons.Settings />
                 <input 
                    type="text" 
                    name="name" 
                    defaultValue={initialBar?.name || ''} 
                    className="bg-transparent border-none text-sm font-medium text-slate-700 placeholder-slate-400 focus:outline-none w-32 sm:w-48 text-right sm:text-left truncate"
                    placeholder="Configurar Nombre Bar"
                 />
               </form>
           </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Hero / Main Action Area */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            
            {/* Left Column: Upload & Send (8 cols) */}
            <div className="lg:col-span-8 space-y-6">
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                    <div className="p-6 sm:p-8">
                        <h2 className="text-2xl font-bold text-slate-900 mb-2">Publicar Nuevo Menú</h2>
                        <p className="text-slate-500 mb-8">Sube el menú del día y notifica a todos tus clientes automáticamente por WhatsApp.</p>
                        
                        <form action={uploadMenu} className="space-y-6">
                           
                           {/* Step 1: Image Upload */}
                           <div className="group relative border-2 border-dashed border-slate-300 rounded-xl bg-slate-50 hover:bg-indigo-50/30 hover:border-indigo-400 transition-all duration-300 cursor-pointer text-center py-12 px-6">
                                <input 
                                    type="file" 
                                    name="menuFile" 
                                    required 
                                    accept="image/*,application/pdf" 
                                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
                                    onChange={(e) => {
                                        const file = e.target.files?.[0];
                                        if (file) setSelectedFileName(file.name);
                                    }}
                                />
                                <div className="pointer-events-none relative z-10 flex flex-col items-center">
                                    <div className="bg-white p-4 rounded-full shadow-sm mb-4 group-hover:scale-110 transition-transform duration-300">
                                        <Icons.Upload />
                                    </div>
                                    <h3 className="text-lg font-semibold text-slate-700 group-hover:text-indigo-700 transition-colors">
                                        {selectedFileName ? selectedFileName : "Arrastra tu imagen aquí"}
                                    </h3>
                                    <p className="text-slate-400 text-sm mt-1">o haz clic para explorar archivos</p>
                                </div>
                           </div>

                             {/* Step 2: Message & Templates */}
                           <div className="space-y-3">
                                <div className="flex justify-between items-end">
                                    <label className="block text-sm font-bold text-slate-700">Mensaje Personalizado</label>
                                    <div className="flex gap-2 text-xs">
                                        {initialTemplates.map(t => (
                                            <button 
                                                key={t.id} 
                                                type="button"
                                                onClick={() => setMessageText(t.content)}
                                                className="bg-slate-100 hover:bg-indigo-100 text-slate-600 hover:text-indigo-700 px-3 py-1.5 rounded-full transition border border-transparent hover:border-indigo-200"
                                            >
                                                {t.name}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                <div className="relative">
                                    <textarea 
                                        name="messageText" 
                                        rows={4} 
                                        className="w-full border border-slate-200 rounded-xl p-4 text-sm focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition resize-none placeholder-slate-400 shadow-sm"
                                        value={messageText}
                                        onChange={(e) => setMessageText(e.target.value)}
                                        placeholder="Escribe tu mensaje aquí..."
                                    ></textarea>
                                    <div className="absolute bottom-3 right-3 text-xs text-slate-400 bg-white px-2 py-1 rounded-md border border-slate-100">
                                        Variable: <code className="text-indigo-500 font-mono">{'{nombre}'}</code>
                                    </div>
                                </div>
                           </div>

                           <button type="submit" className="w-full bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-white py-4 px-6 rounded-xl font-bold text-lg shadow-lg shadow-indigo-500/30 transform hover:-translate-y-0.5 transition-all duration-200 flex items-center justify-center">
                                <Icons.Send />
                                Enviar Menú Ahora
                           </button>
                        </form>
                    </div>
                </div>

                {/* History Section */}
                 <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 sm:p-8">
                     <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center">
                        <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                        Envíos Recientes
                     </h3>
                     <div className="space-y-4">
                        {initialMenus.map(menu => (
                            <div key={menu.id} className="group flex items-center gap-4 p-4 rounded-xl border border-slate-100 hover:border-indigo-100 hover:bg-slate-50 transition">
                                <div className="h-16 w-16 bg-slate-200 rounded-lg overflow-hidden relative shadow-inner">
                                    <img src={menu.imageUrl} className="object-cover w-full h-full" alt="Menu miniature" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-semibold text-slate-900 truncate">Menú del día</p>
                                    <p className="text-xs text-slate-500">{menu.createdAt.toLocaleString('es-ES', { dateStyle: 'long', timeStyle: 'short' })}</p>
                                </div>
                                <a href={menu.imageUrl} target="_blank" className="text-indigo-600 hover:text-indigo-800 p-2 rounded-full hover:bg-indigo-50 transition" title="Ver imagen">
                                    <Icons.Image />
                                </a>
                            </div>
                        ))}
                        {initialMenus.length === 0 && <div className="text-center py-10 text-slate-400">No hay actividad reciente.</div>}
                     </div>
                 </div>
            </div>

            {/* Right Column: Sidebar (4 cols) */}
            <div className="lg:col-span-4 space-y-8">
                
                {/* Templates Manage */}
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                    <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                        <Icons.Template />
                        Plantillas
                    </h3>
                    <div className="space-y-3 mb-6">
                        {initialTemplates.map(t => (
                            <div key={t.id} className="flex justify-between items-center group bg-slate-50 p-3 rounded-lg border border-slate-100 hover:border-indigo-200 transition">
                                <div className="min-w-0 pointer-events-none">
                                    <p className="text-sm font-medium text-slate-700">{t.name}</p>
                                    <p className="text-xs text-slate-400 truncate mt-0.5">{t.content}</p>
                                </div>
                                <form action={deleteMessageTemplate.bind(null, t.id)}>
                                    <button className="text-slate-300 hover:text-red-500 p-1.5 rounded-md hover:bg-red-50 transition"><Icons.Trash /></button>
                                </form>
                            </div>
                        ))}
                        {initialTemplates.length === 0 && <p className="text-sm text-slate-400 italic text-center py-2">No tienes plantillas.</p>}
                    </div>
                    
                    <form action={createMessageTemplate} className="space-y-3 pt-4 border-t border-slate-100">
                        <input type="text" name="name" placeholder="Nueva Plantilla (ej. Viernes)" required className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400 transition" />
                        <textarea name="content" placeholder="Contenido del mensaje..." rows={2} required className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400 transition resize-none"></textarea>
                        <button type="submit" className="w-full bg-slate-900 hover:bg-slate-800 text-white text-sm font-medium py-2.5 rounded-lg transition shadow-sm">Guardar Plantilla</button>
                    </form>
                </div>

                {/* Contacts / Companies */}
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 flex flex-col h-[500px]">
                    <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                        <Icons.Users />
                        Lista de Difusión
                        <span className="bg-indigo-100 text-indigo-700 text-xs py-0.5 px-2 rounded-full ml-auto">{initialCompanies.length}</span>
                    </h3>
                    
                    <div className="flex-1 overflow-y-auto pr-2 space-y-1 mb-4 scrollbar-thin scrollbar-thumb-slate-200 scrollbar-track-transparent">
                        {initialCompanies.map(c => (
                            <div key={c.id} className="flex items-center justify-between p-3 hover:bg-slate-50 rounded-lg transition group">
                                <div>
                                    <p className="text-sm font-semibold text-slate-700">{c.name}</p>
                                    <div className="flex items-center text-xs text-slate-400 gap-2">
                                        <span>{c.contactName}</span>
                                        <span className="w-1 h-1 bg-slate-300 rounded-full"></span>
                                        <span className="font-mono">{c.contactPhone}</span>
                                    </div>
                                </div>
                                <form action={deleteCompany.bind(null, c.id)}>
                                    <button className="text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition p-1"><Icons.Trash /></button>
                                </form>
                            </div>
                        ))}
                    </div>

                    <form action={createCompany} className="pt-4 border-t border-slate-100 space-y-3">
                        <div className="grid grid-cols-2 gap-2">
                            <input type="text" name="name" placeholder="Empresa" required className="text-xs border border-slate-200 rounded-lg px-3 py-2 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500" />
                            <input type="text" name="contactName" placeholder="Contacto" required className="text-xs border border-slate-200 rounded-lg px-3 py-2 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500" />
                        </div>
                        <div className="flex gap-2">
                            <input type="text" name="contactPhone" placeholder="+34 WhatsApp" required className="flex-1 text-xs border border-slate-200 rounded-lg px-3 py-2 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500" />
                            <button type="submit" className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg px-3 transition shadow-sm font-bold"><Icons.Plus /></button>
                        </div>
                    </form>
                </div>

            </div>
        </div>
      </main>
    </div>
  )
}

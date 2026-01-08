import { uploadMenu, createCompany, deleteCompany } from './actions'
import { prisma } from '@/lib/prisma'

export default async function Home() {
  const menus = await prisma.menu.findMany({
    include: { bar: true },
    orderBy: { createdAt: 'desc' }
  })
  
  const companies = await prisma.company.findMany({
    orderBy: { name: 'asc' }
  })

  return (
    <main className="min-h-screen p-8 bg-gray-50 text-gray-900">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 text-center text-blue-800">Distribución de Menús - Polígono</h1>
        
        {/* Upload Section */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-xl font-semibold mb-4">Subir Menú (Solo Bares)</h2>
          <form action={uploadMenu} className="flex flex-col gap-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center bg-gray-50">
              <label className="block mb-2 text-sm font-medium text-gray-900">Seleccionar imagen del menú</label>
              <input type="file" name="menuFile" accept="image/*,application/pdf" className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none"/>
            </div>
            <button type="submit" className="bg-blue-600 text-white py-3 px-4 rounded font-bold hover:bg-blue-700 transition">
              Subir y Enviar a WhatsApp
            </button>
          </form>
        </div>

        {/* Company Management Section */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-xl font-semibold mb-4">Gestionar Empresas Destinatarias</h2>
          
          <div className="overflow-x-auto">
             <table className="min-w-full divide-y divide-gray-200 mb-6">
                <thead>
                    <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Empresa</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contacto</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Teléfono (WhatsApp)</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {companies.map(company => (
                        <tr key={company.id}>
                            <td className="px-6 py-4 whitespace-nowrap">{company.name}</td>
                            <td className="px-6 py-4 whitespace-nowrap">{company.contactName}</td>
                            <td className="px-6 py-4 whitespace-nowrap">{company.contactPhone}</td>
                            <td className="px-6 py-4 whitespace-nowrap">
                                <form action={deleteCompany.bind(null, company.id)}>
                                    <button className="text-red-600 hover:text-red-900">Eliminar</button>
                                </form>
                            </td>
                        </tr>
                    ))}
                    {companies.length === 0 && <tr><td colSpan={4} className="px-6 py-4 text-center text-gray-500">No hay empresas registradas</td></tr>}
                </tbody>
             </table>
          </div>

          <form action={createCompany} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end bg-gray-50 p-4 rounded">
            <div className="flex flex-col">
                <label className="text-sm font-medium text-gray-700 mb-1">Nombre Empresa</label>
                <input type="text" name="name" required className="border border-gray-300 rounded px-3 py-2 text-sm" placeholder="Ej. Transportes SL" />
            </div>
            <div className="flex flex-col">
                <label className="text-sm font-medium text-gray-700 mb-1">Nombre Contacto</label>
                <input type="text" name="contactName" className="border border-gray-300 rounded px-3 py-2 text-sm" placeholder="Ej. Juan" />
            </div>
            <div className="flex flex-col">
                <label className="text-sm font-medium text-gray-700 mb-1">Teléfono</label>
                <input type="text" name="contactPhone" required className="border border-gray-300 rounded px-3 py-2 text-sm" placeholder="Ej. +34600123456" />
            </div>
            <button type="submit" className="bg-green-600 text-white py-2 px-4 rounded font-bold hover:bg-green-700 transition h-10">
              Añadir Empresa
            </button>
          </form>
        </div>

        {/* History Section */}
        <div className="space-y-6">
          <h2 className="text-2xl font-semibold">Menús Enviados Recientemente</h2>
          {menus.map(menu => (
            <div key={menu.id} className="bg-white p-4 rounded shadow flex flex-col md:flex-row items-start gap-4">
              <div className="w-full md:w-48 h-48 bg-gray-100 rounded overflow-hidden flex-shrink-0 border">
                 {/* eslint-disable-next-line @next/next/no-img-element */}
                 <img src={menu.imageUrl} alt="Menu" className="w-full h-full object-contain" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-xl text-blue-900">{menu.bar.name}</h3>
                <p className="text-gray-600">Fecha del Menú: {menu.date.toLocaleDateString()}</p>
                <p className="text-gray-500 text-sm mt-1">Subido el: {menu.createdAt.toLocaleString()}</p>
                <div className="mt-4">
                    <a href={menu.imageUrl} target="_blank" rel="noopener noreferrer" className="inline-block bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-2 px-4 rounded">
                        Ver Menú Completo
                    </a>
                </div>
              </div>
            </div>
          ))}
          {menus.length === 0 && <p className="text-gray-500 text-center py-8">No hay menús subidos aún. ¡Sé el primero!</p>}
        </div>
      </div>
    </main>
  )
}

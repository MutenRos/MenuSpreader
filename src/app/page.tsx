import { prisma } from '@/lib/prisma'
import MenuAppClient from './MenuAppClient'

export const dynamic = 'force-dynamic'

export default async function Home() {
  const bar = await prisma.bar.findFirst()
  
  const templates = bar 
    ? await prisma.messageTemplate.findMany({ where: { barId: bar.id } }) 
    : []

  const menus = await prisma.menu.findMany({
    include: { bar: true },
    orderBy: { createdAt: 'desc' },
    take: 10
  })
  
  const companies = await prisma.company.findMany({
    orderBy: { name: 'asc' }
  })

  return (
    <MenuAppClient 
      initialBar={bar}
      initialTemplates={templates}
      initialCompanies={companies}
      initialMenus={menus}
    />
  )
}

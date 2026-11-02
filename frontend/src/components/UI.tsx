import {ReactNode} from 'react';
export function Card({children,className='' }:{children:ReactNode;className?:string}){return <div className={'card '+className}>{children}</div>}
export function Stat({label,value,sub,icon}:{label:string;value:string|number;sub?:string;icon?:ReactNode}){return <Card className="stat"><div className="stat-top"><span>{label}</span>{icon}</div><strong>{value}</strong>{sub&&<small>{sub}</small>}</Card>}
export function Badge({children}:{children:ReactNode}){return <span className={'badge '+String(children).toLowerCase().replace(/[^a-z0-9]+/g,'-')}>{children}</span>}
export function Progress({value}:{value:number}){return <div className="progress"><i style={{width:`${Math.min(100,value)}%`}}/></div>}
